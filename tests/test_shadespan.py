"""ShadeSpan test suite.

Color math is checked against published reference values (Sharma et al. 2005
CIEDE2000 dataset, WCAG worked examples), scoring against constructed
cases with known-correct direction, and the pipeline end-to-end in mock mode.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shadespan.models import Catalog, Garment, GarmentCategory, Panel, ToneModel  # noqa: E402
from shadespan.scoring import color as C  # noqa: E402
from shadespan.scoring.grade import grade_for, grade_garments, summarize  # noqa: E402
from shadespan.scoring.metrics import score_cell  # noqa: E402


# ------------------------------------------------------------- color math --

def test_delta_e2000_sharma_pairs():
    # Reference pairs from Sharma, Wu & Dalal (2005), Table 1.
    cases = [
        ((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
        ((50.0, 3.1571, -77.2803), (50.0, 0.0, -82.7485), 2.8615),
        ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
        ((50.0, 2.5, 0.0), (50.0, 3.2592, 0.335), 1.0000),
    ]
    for lab1, lab2, expected in cases:
        assert C.delta_e2000(lab1, lab2) == pytest.approx(expected, abs=1e-3)


def test_srgb_lab_roundtrip_anchors():
    l, a, b = C.hex_to_lab("#FFFFFF")
    assert l == pytest.approx(100.0, abs=0.01)
    assert abs(a) < 0.01 and abs(b) < 0.01
    l, _, _ = C.hex_to_lab("#000000")
    assert l == pytest.approx(0.0, abs=0.01)


def test_wcag_contrast_anchors():
    assert C.contrast_ratio(C.hex_to_rgb("#FFFFFF"), C.hex_to_rgb("#000000")) == pytest.approx(21.0, abs=0.01)
    assert C.contrast_ratio(C.hex_to_rgb("#777777"), C.hex_to_rgb("#777777")) == pytest.approx(1.0)


def test_ita_bands_are_ordered():
    panel_hexes = ["#F6E3D6", "#EFC9B0", "#D9A579", "#B07B4F", "#7E4F2A", "#4A2C17"]
    itas = [C.ita_deg(C.hex_to_lab(h)) for h in panel_hexes]
    assert itas == sorted(itas, reverse=True), "ITA must fall as tones deepen"
    assert C.ita_band(60) == "very light" and C.ita_band(-40) == "dark"


# ---------------------------------------------------------------- scoring --

def _garment(hexc: str, sku: str = "G1") -> Garment:
    return Garment(sku=sku, name=sku, category=GarmentCategory.upper_body, hex=hexc, image="x.png")


def _tone(hexc: str, tid: str = "T1") -> ToneModel:
    return ToneModel(id=tid, label=tid, fitzpatrick="III", skin_hex=hexc, image="y.png")


def test_washout_beige_on_fair_flags_and_caps():
    cell = score_cell(_garment("#EFC4B8"), _tone("#F6E3D6"))
    assert cell.washout is True
    assert cell.score <= 39.0
    assert any("Washout" in f for f in cell.flags)


def test_cobalt_scores_high_everywhere():
    # includes #7E4F2A: near-equal luminance, so only chromatic contrast carries it
    for skin in ["#F6E3D6", "#D9A579", "#7E4F2A", "#4A2C17"]:
        cell = score_cell(_garment("#2B4FC7"), _tone(skin))
        assert cell.score >= 65.0, f"cobalt should clear B on {skin}, got {cell.score}"
        assert not cell.washout


def test_chocolate_fails_deep_passes_fair():
    deep = score_cell(_garment("#5A3A26"), _tone("#4A2C17"))
    fair = score_cell(_garment("#5A3A26"), _tone("#F6E3D6"))
    assert deep.score < fair.score
    assert deep.washout is True


def test_fidelity_flag_without_penalty_by_default():
    cell = score_cell(_garment("#2B4FC7"), _tone("#D9A579"), fidelity_delta_e=45.0)
    assert any("fidelity" in f.lower() for f in cell.flags)
    baseline = score_cell(_garment("#2B4FC7"), _tone("#D9A579"))
    assert cell.score == baseline.score  # penalty off by default


def test_fidelity_quiet_within_lighting_noise():
    """A correct render still measures 8-20 dE off its swatch under studio
    lighting; flagging that would cry wolf on most of the matrix."""
    cell = score_cell(_garment("#2B4FC7"), _tone("#D9A579"), fidelity_delta_e=12.0)
    assert not any("fidelity" in f.lower() for f in cell.flags)


# ---------------------------------------------------------------- grading --

def test_grade_bands():
    assert grade_for(85) == "A" and grade_for(70) == "B"
    assert grade_for(55) == "C" and grade_for(45) == "D" and grade_for(10) == "F"


def test_garment_graded_on_worst_tone():
    cat = Catalog(name="t", garments=[_garment("#EFC4B8", "BLUSH")])
    pan = Panel(name="p", models=[_tone("#F6E3D6", "F1"), _tone("#4A2C17", "F6")])
    cells = [score_cell(cat.garments[0], m) for m in pan.models]
    grades = grade_garments(cat, pan, cells)
    assert grades[0].min_score == min(c.score for c in cells)
    assert grades[0].grade == grade_for(grades[0].min_score)


def test_summary_palette_gap_detection():
    # A catalog of only near-skin neutrals should trip a gap on some tone.
    cat = Catalog(name="t", garments=[_garment("#EFC4B8", "A"), _garment("#F1E8DC", "B")])
    pan = Panel(name="p", models=[_tone("#F6E3D6", "F1"), _tone("#EFC9B0", "F2")])
    cells = [score_cell(g, m) for g in cat.garments for m in pan.models]
    grades = grade_garments(cat, pan, cells)
    s = summarize(cat, pan, cells, grades, "mock", "run", 0)
    assert s.palette_gaps, "expected at least one palette gap"


# ------------------------------------------------------------ end-to-end --

def test_mock_pipeline_end_to_end(tmp_path: Path):
    from shadespan.pipeline.orchestrator import run_audit
    from shadespan.report.html import write_report
    from shadespan.youcam.mock import MockYouCamClient

    cat_path = ROOT / "assets" / "catalog" / "catalog.json"
    pan_path = ROOT / "assets" / "models" / "panel.json"
    assert cat_path.exists(), "run scripts/generate_catalog.py first"

    catalog = Catalog.model_validate_json(cat_path.read_text())
    panel = Panel.model_validate_json(pan_path.read_text())
    catalog.garments = catalog.garments[:3]

    client = MockYouCamClient(
        garment_hexes={Path(g.image).name: g.hex for g in catalog.garments},
        panel_hexes={Path(m.image).name: m.skin_hex for m in panel.models},
    )
    report = asyncio.run(run_audit(client, catalog, cat_path.parent, panel, pan_path.parent,
                                   tmp_path, mode="mock"))
    assert len(report.renders) == 3 * 6
    assert all(r.status.value == "ok" for r in report.renders)
    assert report.summary.units_spent == 0

    run_dir = tmp_path / report.summary.run_id
    html = write_report(report, run_dir)
    assert html.exists() and html.stat().st_size > 10_000
    saved = json.loads((run_dir / "audit.json").read_text())
    assert saved["summary"]["run_id"] == report.summary.run_id

    # second run must be fully cache-served
    report2 = asyncio.run(run_audit(client, catalog, cat_path.parent, panel, pan_path.parent,
                                    tmp_path, mode="mock"))
    assert all(r.cached for r in report2.renders)
