"""ShadeSpan dashboard.

Three jobs: start an audit, show progress, open the report. State is a
dict of run threads; runs themselves persist on disk under runs/, so the
dashboard is disposable.
"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
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
    _jobs[job_id] = {"status": "running", "done": 0, "total": 0, "run_id": None, "error": None}

    def work() -> None:
        try:
            cat, cat_dir = _load_catalog(DEFAULT_CATALOG)
            pan, pan_dir = _load_panel(DEFAULT_PANEL)
            client = _make_client(req.live, cat, cat_dir, pan, pan_dir)

            def progress(done: int, total: int) -> None:
                _jobs[job_id].update(done=done, total=total)

            async def _run():
                try:
                    return await run_audit(client, cat, cat_dir, pan, pan_dir, RUNS_DIR,
                                           mode="live" if req.live else "mock",
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
