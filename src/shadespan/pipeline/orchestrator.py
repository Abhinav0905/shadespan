"""Audit orchestration: garments x panel fan-out with a unit budget guard.

Design points that matter at 1,000 units:
  cache    render outputs are content-addressed (sha1 of garment bytes +
           person bytes + category + engine). Re-running an audit re-renders
           nothing that already exists, so a crashed run resumes for free.
  budget   before every live call the ledger projects the spend; the run
           stops cleanly at the cap instead of draining the account.
  bounded  a semaphore keeps concurrency polite (default 3) so the API's
           rate limits and your polling loop stay comfortable.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from pathlib import Path

from ..config import settings
from ..models import (
    AuditReport, Catalog, Garment, Panel, RenderResult, RenderStatus, ToneModel,
)
from ..scoring.fidelity import render_drift
from ..scoring.grade import grade_garments, summarize
from ..scoring.metrics import score_cell

log = logging.getLogger("shadespan.pipeline")


class UnitLedger:
    def __init__(self, cap: int):
        self.cap = cap
        self.spent = 0
        self._lock = asyncio.Lock()

    async def charge(self, units: int) -> bool:
        async with self._lock:
            if self.spent + units > self.cap:
                return False
            self.spent += units
            return True


def _cache_key(garment_path: Path, person_path: Path, category: str, engine: str) -> str:
    h = hashlib.sha1()
    h.update(garment_path.read_bytes())
    h.update(person_path.read_bytes())
    h.update(category.encode())
    h.update(engine.encode())
    return h.hexdigest()[:20]


async def run_audit(
    client,
    catalog: Catalog,
    catalog_dir: Path,
    panel: Panel,
    panel_dir: Path,
    out_dir: Path,
    mode: str,
    max_units: int | None = None,
    skus: list[str] | None = None,
    progress_cb=None,
) -> AuditReport:
    run_id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    run_dir = out_dir / run_id
    renders_dir = run_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / "_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    garments = [g for g in catalog.garments if not skus or g.sku in skus]
    ledger = UnitLedger(max_units if max_units is not None else settings.max_units_per_run)
    sem = asyncio.Semaphore(settings.concurrency)
    total = len(garments) * len(panel.models)
    done = 0

    async def render_one(g: Garment, m: ToneModel) -> RenderResult:
        nonlocal done
        gpath, mpath = g.image_path(catalog_dir), m.image_path(panel_dir)
        key = _cache_key(gpath, mpath, g.category.value, client.name)
        cached_file = cache_dir / f"{key}.png"
        rel = f"renders/{g.sku}__{m.id}.png"
        target = run_dir / rel

        if cached_file.exists():
            target.write_bytes(cached_file.read_bytes())
            res = RenderResult(garment_sku=g.sku, tone_id=m.id, status=RenderStatus.ok,
                               image=rel, engine=client.name, cached=True)
        else:
            live = client.name != "mock"
            units = settings.units_per_vto if live else 0
            if live and not await ledger.charge(units):
                res = RenderResult(garment_sku=g.sku, tone_id=m.id, status=RenderStatus.skipped,
                                   engine=client.name,
                                   error=f"unit budget cap ({ledger.cap}) reached")
            else:
                try:
                    async with sem:
                        img, task_id = await client.try_on(mpath, gpath, g.category.value)
                    target.write_bytes(img)
                    cached_file.write_bytes(img)
                    res = RenderResult(garment_sku=g.sku, tone_id=m.id, status=RenderStatus.ok,
                                       image=rel, engine=client.name, task_id=task_id,
                                       units_charged=units)
                except Exception as exc:  # noqa: BLE001 - recorded per cell, run continues
                    log.warning("render failed %s x %s: %s", g.sku, m.id, exc)
                    res = RenderResult(garment_sku=g.sku, tone_id=m.id,
                                       status=RenderStatus.failed, engine=client.name,
                                       error=str(exc)[:300])
        done += 1
        if progress_cb:
            progress_cb(done, total)
        return res

    tasks = [render_one(g, m) for g in garments for m in panel.models]
    renders = list(await asyncio.gather(*tasks))

    # Scoring is independent of render success: it works from calibrated
    # colors, so a failed render still yields a scored cell (minus fidelity).
    # Where a render did land, measure what colour it actually produced, so a
    # cell that shows contradicting evidence says so instead of staying quiet.
    ok_renders = {(r.garment_sku, r.tone_id): r for r in renders
                  if r.status == RenderStatus.ok and r.image}
    drift: dict[tuple[str, str], float] = {}
    for g in garments:
        for m in panel.models:
            r = ok_renders.get((g.sku, m.id))
            if not r:
                continue
            try:
                de, hexv = render_drift(run_dir / r.image, m.image_path(panel_dir), g.hex)
            except Exception as exc:  # noqa: BLE001 - fidelity is advisory, never fatal
                log.warning("fidelity check failed %s x %s: %s", g.sku, m.id, exc)
                continue
            if de is not None:
                drift[(g.sku, m.id)] = de
                r.rendered_hex = hexv
                r.fidelity_delta_e = round(de, 1)

    cells = [score_cell(g, m, fidelity_delta_e=drift.get((g.sku, m.id)))
             for g in garments for m in panel.models]

    sub_catalog = Catalog(name=catalog.name, brand=catalog.brand, garments=garments)
    grades = grade_garments(sub_catalog, panel, cells)
    summary = summarize(sub_catalog, panel, cells, grades, mode, run_id, ledger.spent)
    report = AuditReport(summary=summary, catalog=sub_catalog, panel=panel,
                         renders=renders, cells=cells, grades=grades)

    (run_dir / "audit.json").write_text(json.dumps(report.model_dump(), indent=2, default=str))
    return report
