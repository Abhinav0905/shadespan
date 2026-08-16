"""Aggregate cell scores into garment grades and a catalog summary.

A garment is graded on its WORST tone, not its average. A shirt that looks
great on five tones and disappears on the sixth is a flagged shirt; averages
hide exactly the customers this tool exists to protect.
"""
from __future__ import annotations

from collections import defaultdict

from ..models import AuditSummary, Catalog, CellScore, GarmentGrade, Panel

GRADE_BANDS = [(80.0, "A"), (65.0, "B"), (50.0, "C"), (35.0, "D")]


def grade_for(min_score: float) -> str:
    for floor, letter in GRADE_BANDS:
        if min_score >= floor:
            return letter
    return "F"


def grade_garments(catalog: Catalog, panel: Panel, cells: list[CellScore]) -> list[GarmentGrade]:
    by_sku: dict[str, list[CellScore]] = defaultdict(list)
    for c in cells:
        by_sku[c.garment_sku].append(c)

    tone_label = {m.id: m.label for m in panel.models}
    grades: list[GarmentGrade] = []
    for g in catalog.garments:
        gcells = by_sku.get(g.sku, [])
        if not gcells:
            continue
        min_score = min(c.score for c in gcells)
        mean_score = sum(c.score for c in gcells) / len(gcells)
        worst = sorted(gcells, key=lambda c: c.score)[:2]
        flags = [f for c in gcells for f in c.flags]
        grades.append(
            GarmentGrade(
                garment_sku=g.sku,
                grade=grade_for(min_score),
                min_score=round(min_score, 1),
                mean_score=round(mean_score, 1),
                worst_tones=[tone_label.get(c.tone_id, c.tone_id) for c in worst],
                flags=flags,
            )
        )
    return grades


def summarize(
    catalog: Catalog,
    panel: Panel,
    cells: list[CellScore],
    grades: list[GarmentGrade],
    mode: str,
    run_id: str,
    units_spent: int,
) -> AuditSummary:
    counts: dict[str, int] = defaultdict(int)
    for g in grades:
        counts[g.grade] += 1
    ok = sum(1 for g in grades if g.grade in ("A", "B"))
    coverage = 100.0 * ok / len(grades) if grades else 0.0

    # Palette gap analysis: for each tone, does the catalog offer enough
    # garments that clear grade B on that tone specifically?
    gaps: list[str] = []
    by_tone: dict[str, list[CellScore]] = defaultdict(list)
    for c in cells:
        by_tone[c.tone_id].append(c)
    for m in panel.models:
        tcells = by_tone.get(m.id, [])
        if not tcells:
            continue
        good = sum(1 for c in tcells if c.score >= 65.0)
        share = good / len(tcells)
        if share < 0.5:
            gaps.append(
                f"Only {good} of {len(tcells)} garments clear grade B on {m.label} "
                f"({share:.0%}). The palette under-serves this tone."
            )
    return AuditSummary(
        catalog_name=catalog.name,
        panel_name=panel.name,
        mode=mode,
        run_id=run_id,
        coverage_pct=round(coverage, 1),
        grade_counts=dict(counts),
        palette_gaps=gaps,
        units_spent=units_spent,
    )
