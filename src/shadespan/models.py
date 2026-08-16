"""Domain models for ShadeSpan.

Everything the pipeline passes around is defined here so the orchestrator,
scoring engine and report renderer agree on one vocabulary.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class GarmentCategory(str, Enum):
    upper_body = "upper_body"
    lower_body = "lower_body"
    full_body = "full_body"
    dresses = "dresses"


class Garment(BaseModel):
    sku: str
    name: str
    category: GarmentCategory = GarmentCategory.upper_body
    hex: str = Field(description="Dominant garment color as #RRGGBB from the catalog")
    price_usd: Optional[float] = None
    image: str = Field(description="Path to the product photo, relative to the catalog file")

    def image_path(self, catalog_dir: Path) -> Path:
        return (catalog_dir / self.image).resolve()


class Catalog(BaseModel):
    name: str
    brand: str = "Demo Brand"
    garments: list[Garment]


class ToneModel(BaseModel):
    """One member of the skin-tone panel the catalog is audited against."""

    id: str
    label: str = Field(description="Human-readable label, e.g. 'Fitzpatrick III'")
    fitzpatrick: str = Field(description="I..VI")
    skin_hex: str = Field(description="Calibrated skin color as #RRGGBB")
    image: str = Field(description="Path to the model photo, relative to the panel file")
    source: str = Field(
        default="declared",
        description="Where skin_hex came from: declared | sampled | youcam-color-analysis",
    )

    def image_path(self, panel_dir: Path) -> Path:
        return (panel_dir / self.image).resolve()


class Panel(BaseModel):
    name: str
    models: list[ToneModel]


class RenderStatus(str, Enum):
    ok = "ok"
    failed = "failed"
    skipped = "skipped"


class RenderResult(BaseModel):
    garment_sku: str
    tone_id: str
    status: RenderStatus
    image: Optional[str] = None  # path relative to run dir
    engine: str = "mock"
    task_id: Optional[str] = None
    error: Optional[str] = None
    cached: bool = False
    units_charged: int = 0
    rendered_hex: Optional[str] = Field(
        default=None, description="Colour the try-on actually painted, sampled from the render"
    )
    fidelity_delta_e: Optional[float] = Field(
        default=None, description="dE2000 between catalog hex and rendered_hex"
    )


class CellScore(BaseModel):
    garment_sku: str
    tone_id: str
    score: float = Field(ge=0, le=100)
    contrast_ratio: float
    delta_l: float = Field(description="|L*garment - L*skin| in CIELAB")
    hue_gap_deg: float = Field(description="Smallest hue-angle gap garment vs skin, degrees")
    skin_delta_e: float = Field(default=0.0, description="dE2000 garment color vs skin color")
    garment_chroma: float
    washout: bool
    fidelity_delta_e: Optional[float] = Field(
        default=None, description="dE2000 catalog hex vs rendered garment color (experimental)"
    )
    flags: list[str] = Field(default_factory=list)


class GarmentGrade(BaseModel):
    garment_sku: str
    grade: str
    min_score: float
    mean_score: float
    worst_tones: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)


class AuditSummary(BaseModel):
    catalog_name: str
    panel_name: str
    mode: str
    run_id: str
    coverage_pct: float = Field(description="Share of garments graded B or better on every tone")
    grade_counts: dict[str, int]
    palette_gaps: list[str] = Field(default_factory=list)
    units_spent: int = 0


class AuditReport(BaseModel):
    summary: AuditSummary
    catalog: Catalog
    panel: Panel
    renders: list[RenderResult]
    cells: list[CellScore]
    grades: list[GarmentGrade]
