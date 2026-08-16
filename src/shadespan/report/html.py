"""Render an AuditReport into one self-contained HTML file.

Thumbnails are inlined as base64 so the report survives email, Slack and
judges opening it from a zip with no server running. Pass embed=False to
reference render files on disk instead (smaller file, needs the run dir).
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from PIL import Image

from ..models import AuditReport
from ..scoring import color as C

_env = Environment(
    loader=PackageLoader("shadespan.report", "templates"),
    autoescape=select_autoescape(["html"]),
)


def _thumb_b64(path: Path, width: int = 210) -> str:
    img = Image.open(path)
    ratio = width / img.width
    img = img.convert("RGB").resize((width, max(1, int(img.height * ratio))))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=72)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def score_band(score: float) -> str:
    if score >= 80:
        return "pass"
    if score >= 65:
        return "good"
    if score >= 50:
        return "warn"
    return "fail"


def render_html(report: AuditReport, run_dir: Path, embed: bool = True) -> str:
    render_map = {(r.garment_sku, r.tone_id): r for r in report.renders}
    cell_map = {(c.garment_sku, c.tone_id): c for c in report.cells}
    grade_map = {g.garment_sku: g for g in report.grades}

    tones = []
    for m in report.panel.models:
        lab = C.hex_to_lab(m.skin_hex)
        tones.append({"m": m, "ita": round(C.ita_deg(lab), 1), "band": C.ita_band(C.ita_deg(lab))})

    rows = []
    for g in report.catalog.garments:
        cells = []
        for m in report.panel.models:
            cs = cell_map.get((g.sku, m.id))
            rr = render_map.get((g.sku, m.id))
            src = None
            if rr and rr.image:
                p = run_dir / rr.image
                if p.exists():
                    src = _thumb_b64(p) if embed else rr.image
            cells.append({"score": cs, "img": src, "band": score_band(cs.score) if cs else "fail",
                          "render": rr})
        rows.append({"g": g, "grade": grade_map.get(g.sku), "cells": cells})

    worst = sorted(report.grades, key=lambda x: x.min_score)[:3]
    tpl = _env.get_template("report.html.j2")
    return tpl.render(r=report, rows=rows, tones=tones, worst=worst, band=score_band)


def write_report(report: AuditReport, run_dir: Path, embed: bool = True) -> Path:
    out = run_dir / "report.html"
    out.write_text(render_html(report, run_dir, embed=embed))
    return out
