"""Generate the bundled demo assets.

Two things come out of this script, both fully synthetic and license-free:

1. assets/catalog/    14 flat-lay garment product photos (PIL-drawn tees,
                      dresses and long-sleeves with shading, fabric grain and
                      a soft shadow) plus catalog.json. The palette is chosen
                      to make the audit interesting: some colors are near-skin
                      neutrals that should fail on specific tones, some are
                      saturated universals that should pass everywhere.

2. assets/models/     panel.json with six calibrated Fitzpatrick I..VI skin
                      hexes, plus illustrated placeholder figures used ONLY by
                      mock mode. For a live run you drop six real, openly
                      licensed photos in this folder and point panel.json at
                      them (see assets/models/README.md).

Run:  python scripts/generate_catalog.py
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "assets" / "catalog"
MODELS_DIR = ROOT / "assets" / "models"

W = H = 1024

GARMENTS = [
    # sku, name, category, hex, price
    ("TEE-IVORY", "Ivory Crew Tee", "upper_body", "#F1E8DC", 24),
    ("TEE-BLUSH", "Blush Crew Tee", "upper_body", "#EFC4B8", 24),
    ("TEE-PALEYELLOW", "Pale Yellow Crew Tee", "upper_body", "#F2E3A1", 24),
    ("TEE-CAMEL", "Camel Crew Tee", "upper_body", "#C19A6B", 26),
    ("TEE-OLIVE", "Olive Crew Tee", "upper_body", "#6B7345", 26),
    ("TEE-COBALT", "Cobalt Crew Tee", "upper_body", "#2B4FC7", 26),
    ("TEE-EMERALD", "Emerald Crew Tee", "upper_body", "#0E7C5B", 26),
    ("TEE-RUST", "Rust Crew Tee", "upper_body", "#B4552D", 26),
    ("TEE-CHARCOAL", "Charcoal Crew Tee", "upper_body", "#33383D", 24),
    ("TEE-WHITE", "Optic White Crew Tee", "upper_body", "#FAFAFA", 22),
    ("LS-CHOCOLATE", "Chocolate Long Sleeve", "upper_body", "#5A3A26", 32),
    ("LS-SAGE", "Sage Long Sleeve", "upper_body", "#A8B79A", 32),
    ("DRS-DUSTYPINK", "Dusty Pink Shift Dress", "dresses", "#D8A7A0", 58),
    ("DRS-BLACK", "Jet Black Shift Dress", "dresses", "#17181A", 58),
]

# Calibrated panel: representative sRGB values per Fitzpatrick band. In a real
# audit these get replaced by values sampled from the actual model photos
# (shadespan panel sample) or returned by YouCam color analysis.
PANEL = [
    ("F1", "Fitzpatrick I", "I", "#F6E3D6"),
    ("F2", "Fitzpatrick II", "II", "#EFC9B0"),
    ("F3", "Fitzpatrick III", "III", "#D9A579"),
    ("F4", "Fitzpatrick IV", "IV", "#B07B4F"),
    ("F5", "Fitzpatrick V", "V", "#7E4F2A"),
    ("F6", "Fitzpatrick VI", "VI", "#4A2C17"),
]


def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _shade(rgb: tuple[int, int, int], k: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, round(c * k))) for c in rgb)  # type: ignore[return-value]


def _tee_outline(long_sleeve: bool) -> list[tuple[float, float]]:
    """Symmetric tee silhouette on a 1000x1000 grid, centered."""
    cx = 500
    neck_w, shoulder_x, shoulder_y = 90, 320, 200
    sleeve_x = 470 if not long_sleeve else 480
    sleeve_y = 380 if not long_sleeve else 720
    pit_x, pit_y = 300, 400 if not long_sleeve else 430
    hem_x, hem_y = 280, 860
    right = [
        (cx + neck_w, 150),
        (cx + shoulder_x, shoulder_y),
        (cx + sleeve_x, sleeve_y),
        (cx + sleeve_x - 110, sleeve_y + 55),
        (cx + pit_x, pit_y),
        (cx + hem_x, hem_y),
    ]
    left = [(2 * cx - x, y) for x, y in reversed(right)]
    return right + [(cx + hem_x - 40, 900), (cx - hem_x + 40, 900)] + left


def _dress_outline() -> list[tuple[float, float]]:
    cx = 500
    right = [
        (cx + 80, 130),
        (cx + 250, 190),
        (cx + 330, 330),
        (cx + 230, 360),
        (cx + 190, 430),
        (cx + 330, 920),
    ]
    left = [(2 * cx - x, y) for x, y in reversed(right)]
    return right + [(cx + 320, 950), (cx - 320, 950)] + left


def draw_garment(hex_color: str, category: str, long_sleeve: bool, seed: int) -> Image.Image:
    rng = random.Random(seed)
    base = _hex_rgb(hex_color)
    img = Image.new("RGB", (W, H), (250, 250, 249))
    d = ImageDraw.Draw(img)

    pts = _dress_outline() if category == "dresses" else _tee_outline(long_sleeve)
    pts = [(x * W / 1000, y * H / 1000) for x, y in pts]

    # soft drop shadow
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).polygon([(x + 14, y + 20) for x, y in pts], fill=70)
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    img.paste(Image.new("RGB", (W, H), (208, 206, 202)), (0, 0), sh)

    # body fill
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    fill = Image.new("RGB", (W, H), base)

    # vertical shading + a few fold streaks, then fabric grain
    arr = np.asarray(fill).astype(np.float32)
    yy = np.linspace(-1, 1, H)[:, None]
    shade = 1.0 - 0.10 * (yy**2)
    for _ in range(6):
        fx = rng.uniform(0.15, 0.85) * W
        fw = rng.uniform(18, 42)
        xs = np.arange(W)[None, :]
        streak = 0.05 * np.exp(-((xs - fx) ** 2) / (2 * fw**2))
        shade = shade - streak
    arr *= shade[..., None] if shade.ndim == 2 else shade
    noise = np.random.default_rng(seed).normal(0, 2.2, (H, W, 1))
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    fill = Image.fromarray(arr)
    img.paste(fill, (0, 0), mask)

    # collar
    cx = W / 2
    collar = _shade(base, 0.82)
    d = ImageDraw.Draw(img)
    d.arc([cx - 95, 105, cx + 95, 215], start=0, end=180, fill=collar, width=14)

    # seam hints
    seam = _shade(base, 0.88)
    if category != "dresses":
        d.line([(cx - 285, 415), (cx - 260, 880)], fill=seam, width=3)
        d.line([(cx + 285, 415), (cx + 260, 880)], fill=seam, width=3)
    return img


def draw_mock_model(skin_hex: str, label: str) -> Image.Image:
    """Illustrated placeholder figure used only by mock mode. Deliberately
    flat and non-photographic so nobody mistakes it for a real render."""
    w, h = 768, 1024
    skin = _hex_rgb(skin_hex)
    img = Image.new("RGB", (w, h), (240, 239, 236))
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(h * 0.62), w, h], fill=(229, 227, 222))
    cx = w // 2
    # neck + head
    d.rounded_rectangle([cx - 34, 258, cx + 34, 330], 18, fill=_shade(skin, 0.94))
    d.ellipse([cx - 92, 96, cx + 92, 296], fill=skin)
    d.ellipse([cx - 40, 170, cx - 22, 192], fill=_shade(skin, 0.72))
    d.ellipse([cx + 22, 170, cx + 40, 192], fill=_shade(skin, 0.72))
    # arms
    d.rounded_rectangle([cx - 205, 330, cx - 135, 720], 34, fill=skin)
    d.rounded_rectangle([cx + 135, 330, cx + 205, 720], 34, fill=skin)
    # torso placeholder (garment gets composited over this in the mock renderer)
    d.rounded_rectangle([cx - 150, 316, cx + 150, 760], 42, fill=(206, 204, 199))
    d.text((24, h - 44), f"{label} - illustrated stand-in", fill=(120, 118, 114))
    return img


def main() -> None:
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    garments = []
    for i, (sku, name, category, hexc, price) in enumerate(GARMENTS):
        fname = f"{sku.lower()}.png"
        draw_garment(hexc, category, sku.startswith("LS-"), seed=41 + i).save(CATALOG_DIR / fname)
        garments.append(
            {
                "sku": sku,
                "name": name,
                "category": category,
                "hex": hexc,
                "price_usd": price,
                "image": fname,
            }
        )
    (CATALOG_DIR / "catalog.json").write_text(
        json.dumps(
            {"name": "ShadeSpan Demo Catalog SS26", "brand": "Meridian Basics", "garments": garments},
            indent=2,
        )
    )

    models = []
    for mid, label, fitz, skin_hex in PANEL:
        fname = f"{mid.lower()}_mock.png"
        draw_mock_model(skin_hex, label).save(MODELS_DIR / fname)
        models.append(
            {
                "id": mid,
                "label": label,
                "fitzpatrick": fitz,
                "skin_hex": skin_hex,
                "image": fname,
                "source": "declared",
            }
        )
    (MODELS_DIR / "panel.json").write_text(
        json.dumps({"name": "Fitzpatrick I-VI reference panel", "models": models}, indent=2)
    )
    print(f"wrote {len(garments)} garments -> {CATALOG_DIR}")
    print(f"wrote {len(models)} panel members -> {MODELS_DIR}")


if __name__ == "__main__":
    main()
