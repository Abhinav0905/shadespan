"""ShadeSpan dashboard.

Three jobs: start an audit, show progress, open the report. State is a
dict of run threads; runs themselves persist on disk under runs/, so the
dashboard is disposable.
"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from ..cli import DEFAULT_CATALOG, DEFAULT_PANEL, _load_catalog, _load_panel, _make_client
from ..config import settings
from ..pipeline.orchestrator import run_audit
from ..report.html import write_report

app = FastAPI(title="ShadeSpan")
RUNS_DIR = Path(settings.runs_dir)
STATIC = Path(__file__).parent / "static"

_jobs: dict[str, dict] = {}


class StartAudit(BaseModel):
    live: bool = False
    skus: list[str] | None = None
    max_units: int | None = None


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC / "index.html").read_text()


@app.get("/api/catalog")
def get_catalog():
    cat, _ = _load_catalog(DEFAULT_CATALOG)
    pan, _ = _load_panel(DEFAULT_PANEL)
    return {"catalog": cat.model_dump(), "panel": pan.model_dump(),
            "units_per_vto": settings.units_per_vto}


@app.post("/api/runs")
def start_run(req: StartAudit):
    job_id = f"job-{len(_jobs) + 1}"
    # A full catalogue audit is 84 renders. On a hosted instance running to a
    # fixed allowance that is never a visitor's to spend, so it runs offline.
    # Downgrading beats capping: a capped run returns 84 "skipped" cells and
    # an empty report, which reads as broken rather than protected.
    live = req.live and settings.public_unit_budget <= 0
    downgraded = req.live and not live
    _jobs[job_id] = {"status": "running", "done": 0, "total": 0, "run_id": None,
                     "error": None, "live": live, "downgraded": downgraded}

    def work() -> None:
        try:
            cat, cat_dir = _load_catalog(DEFAULT_CATALOG)
            pan, pan_dir = _load_panel(DEFAULT_PANEL)
            client = _make_client(live, cat, cat_dir, pan, pan_dir)

            def progress(done: int, total: int) -> None:
                _jobs[job_id].update(done=done, total=total)

            async def _run():
                try:
                    return await run_audit(client, cat, cat_dir, pan, pan_dir, RUNS_DIR,
                                           mode="live" if live else "mock",
                                           max_units=req.max_units, skus=req.skus,
                                           progress_cb=progress)
                finally:
                    await client.aclose()

            report = asyncio.run(_run())
            write_report(report, RUNS_DIR / report.summary.run_id)
            _jobs[job_id].update(status="done", run_id=report.summary.run_id,
                                 summary=report.summary.model_dump())
        except Exception as exc:  # noqa: BLE001
            _jobs[job_id].update(status="error", error=str(exc)[:500])

    threading.Thread(target=work, daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/runs/{job_id}")
def run_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job")
    return JSONResponse(job)


@app.get("/runs/{run_id}/report")
def report(run_id: str):
    path = RUNS_DIR / run_id / "report.html"
    if not path.exists():
        raise HTTPException(404, "report not found")
    return FileResponse(path)


# ------------------------------------------------------------ drop a garment
# One garment against the whole panel. The catalog audit answers "which of my
# products fail"; this answers "would this one" for something not in the
# catalog yet - a sample, a supplier photo, a colourway still being decided.
# Six renders, so roughly 12 units and under half a minute.

TRYON_DIR = RUNS_DIR / "_tryon"

# Units this process has spent on drop-in try-ons. Compared against
# settings.public_unit_budget so a hosted instance degrades to mock instead of
# draining the account. Process-local on purpose: a restart is a fresh budget,
# which is the right behaviour for a demo box and the wrong one for billing.
_spent_units = 0


def _budget() -> dict:
    """How much of the public allowance is left, for the UI to show."""
    cap = settings.public_unit_budget
    if cap <= 0:
        return {"capped": False, "live_available": True}
    left = max(0, cap - _spent_units)
    return {"capped": True, "cap": cap, "spent": _spent_units, "left": left,
            "live_available": left >= settings.units_per_vto * 6}


@app.get("/api/budget")
def budget():
    return _budget()


@app.post("/api/tryon")
async def start_tryon(
    file: UploadFile = File(...),
    live: bool = Form(True),
    category: str = Form("upper_body"),
):
    from ..models import Garment, GarmentCategory
    from ..scoring.swatch import dominant_garment_hex

    job_id = f"tryon-{len(_jobs) + 1}"
    job_dir = TRYON_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "garment.png").suffix.lower() or ".png"
    if suffix not in (".png", ".jpg", ".jpeg", ".webp"):
        raise HTTPException(400, "garment must be a png, jpg or webp image")
    garment_path = job_dir / f"garment{suffix}"
    garment_path.write_bytes(await file.read())

    try:
        garment_hex = dominant_garment_hex(garment_path)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"could not read that image: {exc}") from exc

    try:
        cat = GarmentCategory(category)
    except ValueError:
        cat = GarmentCategory.upper_body

    garment = Garment(sku="DROPPED", name=Path(file.filename or "Dropped garment").stem,
                      category=cat, hex=garment_hex, image=garment_path.name)

    pan, pan_dir = _load_panel(DEFAULT_PANEL)

    # Downgrade rather than refuse: a visitor who arrives after the allowance
    # is gone should still see the whole interaction, just rendered offline.
    downgraded = False
    if live and not _budget()["live_available"]:
        live, downgraded = False, True

    _jobs[job_id] = {
        "status": "running", "done": 0, "total": len(pan.models),
        "garment_hex": garment_hex, "garment_name": garment.name,
        "cells": [], "grade": None, "units": 0, "error": None,
        "live": live, "downgraded": downgraded,
    }

    def work() -> None:
        try:
            asyncio.run(_tryon(job_id, job_dir, garment, garment_path, pan, pan_dir, live))
        except Exception as exc:  # noqa: BLE001
            _jobs[job_id].update(status="error", error=str(exc)[:400])

    threading.Thread(target=work, daemon=True).start()
    return {"job_id": job_id, "garment_hex": garment_hex}


async def _tryon(job_id, job_dir, garment, garment_path, pan, pan_dir, live) -> None:
    from ..scoring.fidelity import render_drift
    from ..scoring.grade import grade_for
    from ..scoring.metrics import score_cell

    cat_stub, _ = _load_catalog(DEFAULT_CATALOG)
    client = _make_client(live, cat_stub, garment_path.parent, pan, pan_dir)
    # The mock engine paints by filename, so teach it this one.
    if hasattr(client, "_garment_hexes"):
        client._garment_hexes[garment_path.name] = garment.hex

    job = _jobs[job_id]
    sem = asyncio.Semaphore(settings.concurrency)

    async def one(model):
        person = model.image_path(pan_dir)
        cell = {"tone_id": model.id, "label": model.label, "fitzpatrick": model.fitzpatrick,
                "skin_hex": model.skin_hex}
        try:
            async with sem:
                img, _task = await client.try_on(person, garment_path, garment.category.value)
            out = job_dir / f"{model.id}.png"
            out.write_bytes(img)
            drift = None
            try:
                drift, _hex = render_drift(out, person, garment.hex)
            except Exception:  # noqa: BLE001 - advisory only
                pass
            score = score_cell(garment, model, fidelity_delta_e=drift)
            cell.update(image=f"/api/tryon/{job_id}/render/{model.id}.png",
                        score=score.score, contrast=score.contrast_ratio,
                        delta_e=score.skin_delta_e, washout=score.washout,
                        flags=score.flags, grade=grade_for(score.score))
            if live:
                global _spent_units
                _spent_units += settings.units_per_vto
                job["units"] = job.get("units", 0) + settings.units_per_vto
        except Exception as exc:  # noqa: BLE001 - one tone must not kill the panel
            cell.update(error=str(exc)[:200])
        job["cells"].append(cell)
        job["done"] = len(job["cells"])
        return cell

    try:
        cells = await asyncio.gather(*(one(m) for m in pan.models))
    finally:
        await client.aclose()

    order = {m.id: i for i, m in enumerate(pan.models)}
    job["cells"] = sorted(cells, key=lambda c: order[c["tone_id"]])
    scored = [c["score"] for c in cells if "score" in c]
    job["grade"] = grade_for(min(scored)) if scored else None
    job["min_score"] = min(scored) if scored else None
    job["worst"] = min((c for c in cells if "score" in c),
                       key=lambda c: c["score"], default={}).get("label")
    job["status"] = "done"


@app.get("/api/tryon/{job_id}")
def tryon_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job")
    return JSONResponse(job)


@app.get("/api/tryon/{job_id}/render/{name}")
def tryon_render(job_id: str, name: str):
    path = TRYON_DIR / job_id / Path(name).name
    if not path.exists():
        raise HTTPException(404, "render not found")
    return FileResponse(path)
