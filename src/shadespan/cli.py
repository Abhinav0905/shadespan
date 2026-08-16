"""ShadeSpan command line.

  shadespan audit    run a catalog audit (mock by default, --live for real)
  shadespan serve    start the dashboard
  shadespan smoke    one live round-trip per API to verify credentials/payloads
  shadespan panel    sample or calibrate panel skin hexes
  shadespan catalog  regenerate the bundled demo assets
"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from .config import settings
from .models import Catalog, Panel

app = typer.Typer(add_completion=False, no_args_is_help=True)
panel_app = typer.Typer(no_args_is_help=True)
app.add_typer(panel_app, name="panel", help="Panel calibration tools")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "assets" / "catalog" / "catalog.json"
DEFAULT_PANEL = ROOT / "assets" / "models" / "panel.json"


def _load_catalog(path: Path) -> tuple[Catalog, Path]:
    return Catalog.model_validate_json(path.read_text()), path.parent


def _load_panel(path: Path) -> tuple[Panel, Path]:
    return Panel.model_validate_json(path.read_text()), path.parent


def _make_client(live: bool, catalog: Catalog, catalog_dir: Path, panel: Panel, panel_dir: Path):
    if live:
        from .youcam.client import YouCamClient
        return YouCamClient()
    from .youcam.mock import MockYouCamClient
    return MockYouCamClient(
        garment_hexes={Path(g.image).name: g.hex for g in catalog.garments},
        panel_hexes={Path(m.image).name: m.skin_hex for m in panel.models},
    )


@app.command()
def audit(
    catalog: Path = typer.Option(DEFAULT_CATALOG, help="Path to catalog.json"),
    panel: Path = typer.Option(DEFAULT_PANEL, help="Path to panel.json"),
    live: bool = typer.Option(False, help="Use the real YouCam API (spends units)"),
    out: Path = typer.Option(Path(settings.runs_dir), help="Runs directory"),
    skus: Optional[str] = typer.Option(None, help="Comma-separated SKU subset"),
    max_units: Optional[int] = typer.Option(None, help="Unit cap for this run"),
    no_embed: bool = typer.Option(False, help="Reference render files instead of inlining"),
):
    """Render every garment on every tone, score, grade and write the report."""
    from .pipeline.orchestrator import run_audit
    from .report.html import write_report

    cat, cat_dir = _load_catalog(catalog)
    pan, pan_dir = _load_panel(panel)
    client = _make_client(live, cat, cat_dir, pan, pan_dir)
    sku_list = [s.strip() for s in skus.split(",")] if skus else None

    n_cells = len([g for g in cat.garments if not sku_list or g.sku in sku_list]) * len(pan.models)
    if live:
        projected = n_cells * settings.units_per_vto
        typer.echo(f"live run: {n_cells} renders, projected <= {projected} units "
                   f"(cap {max_units or settings.max_units_per_run}); cached cells are free")

    def progress(done: int, total: int) -> None:
        typer.echo(f"\r  renders {done}/{total}", nl=(done == total))

    async def _run():
        try:
            return await run_audit(client, cat, cat_dir, pan, pan_dir, out,
                                   mode="live" if live else "mock",
                                   max_units=max_units, skus=sku_list, progress_cb=progress)
        finally:
            await client.aclose()

    report = asyncio.run(_run())
    run_dir = out / report.summary.run_id
    html_path = write_report(report, run_dir, embed=not no_embed)
    typer.echo(f"coverage: {report.summary.coverage_pct}% at grade B+ across all tones")
    typer.echo(f"grades:   {report.summary.grade_counts}")
    typer.echo(f"units:    {report.summary.units_spent}")
    typer.echo(f"report:   {html_path}")


@app.command()
def smoke(
    person: Path = typer.Argument(..., help="A real, openly licensed model photo"),
    garment: Path = typer.Option(DEFAULT_CATALOG.parent / "tee-cobalt.png", help="Garment photo"),
):
    """One live call per API. Run this FIRST with your keys; it prints raw
    responses so any payload-field mismatch against the docs is obvious."""
    subprocess.run([sys.executable, str(ROOT / "scripts" / "smoke_test.py"),
                    str(person), str(garment)], check=False)


@panel_app.command("sample")
def panel_sample(
    panel: Path = typer.Option(DEFAULT_PANEL),
    box: str = typer.Option("center-face", help="'x,y,w,h' pixel box or 'center-face'"),
):
    """Estimate each member's skin hex by sampling their photo locally.
    Free, offline, good enough for the audit; use calibrate --live for
    YouCam-measured values."""
    from PIL import Image
    import numpy as np
    from .scoring.color import rgb_to_hex

    pan, pan_dir = _load_panel(panel)
    for m in pan.models:
        img = Image.open(m.image_path(pan_dir)).convert("RGB")
        w, h = img.size
        if box == "center-face":
            bx, by, bw, bh = int(w * 0.42), int(h * 0.16), int(w * 0.16), int(h * 0.10)
        else:
            bx, by, bw, bh = (int(v) for v in box.split(","))
        arr = np.asarray(img.crop((bx, by, bx + bw, by + bh))).reshape(-1, 3)
        med = np.median(arr, axis=0) / 255.0
        m.skin_hex = rgb_to_hex(tuple(med))
        m.source = "sampled"
        typer.echo(f"{m.id} {m.label}: {m.skin_hex}")
    panel.write_text(pan.model_dump_json(indent=2))
    typer.echo(f"updated {panel}")


@panel_app.command("analyze")
def panel_analyze(panel: Path = typer.Option(DEFAULT_PANEL),
                  out: Path = typer.Option(Path("runs/skin_analysis.json"))):
    """Run YouCam Skin AI analysis over each panel member (live, spends units)
    and save the raw per-member results beside the audit.

    Skin tone itself comes from `panel sample`: the API exposes no
    color-analysis feature, so tone is measured locally from the photo.
    """
    from .youcam.client import YouCamClient

    pan, pan_dir = _load_panel(panel)
    collected: dict[str, dict] = {}

    async def _run():
        client = YouCamClient()
        try:
            for m in pan.models:
                try:
                    scores = await client.skin_analysis_scores(m.image_path(pan_dir))
                    collected[m.id] = scores
                    top = ", ".join(f"{k} {v}" for k, v in list(scores.items())[:5])
                    typer.echo(f"{m.id} {m.label}: {top}")
                except Exception as exc:  # noqa: BLE001 - one member must not kill the run
                    typer.echo(f"{m.id} {m.label}: FAILED {exc}")
        finally:
            await client.aclose()

    asyncio.run(_run())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(collected, indent=2, default=str))
    typer.echo(f"wrote {out}")


@app.command()
def credit():
    """Print the real remaining unit balance on the YouCam account."""
    from .youcam.client import YouCamClient

    async def _run():
        client = YouCamClient()
        try:
            typer.echo(f"{await client.credit_balance():.0f} units remaining")
        finally:
            await client.aclose()

    asyncio.run(_run())


@app.command()
def catalog():
    """Regenerate the bundled synthetic catalog and mock panel."""
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_catalog.py")], check=True)


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8787):
    """Start the dashboard."""
    import uvicorn
    uvicorn.run("shadespan.server.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
