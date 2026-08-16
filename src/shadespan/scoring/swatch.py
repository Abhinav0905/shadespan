"""Read a garment's colour out of a product photo.

Catalog entries declare their hex, but an image dropped into the dashboard
arrives with nothing but pixels, and every downstream score depends on getting
one colour out of it.

A product shot is mostly background. Naively averaging the frame returns
something close to studio white, so the background has to go first: fully
transparent pixels where there is an alpha channel, and near-white, near-grey
low-saturation pixels where there is not. What remains is fabric plus shadow,
and shadow is the second trap - a median over all of it reads darker than the
garment a shopper sees, so the sample is taken from the lit middle of the
remaining luminance range.

Highly desaturated garments (white, ivory, light grey) are the awkward case,
because the background test and the garment look alike. The central-region
fallback exists for exactly those: near the middle of a product shot, whatever
is there is the product.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .color import rgb_to_hex

# Below this alpha a pixel is cut-out background, not fabric.
ALPHA_FLOOR = 40

# A pixel this bright and this close to neutral is studio backdrop.
BACKDROP_LUMA = 232
BACKDROP_SPREAD = 12

MIN_FABRIC_PIXELS = 1500


def dominant_garment_hex(path: Path) -> str:
    """Best estimate of the garment's colour in a product photo."""
    img = Image.open(path).convert("RGBA")
    img.thumbnail((700, 700))  # sampling does not need full resolution
    a = np.asarray(img).astype(float)
    rgb, alpha = a[:, :, :3], a[:, :, 3]

    h, w = alpha.shape
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    luma = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    fabric = (alpha > ALPHA_FLOOR) & ~((luma > BACKDROP_LUMA) & (spread < BACKDROP_SPREAD))

    if int(fabric.sum()) < MIN_FABRIC_PIXELS:
        # Pale garment against a pale backdrop: trust position instead of colour.
        fabric = np.zeros_like(fabric)
        fabric[int(h * 0.35):int(h * 0.65), int(w * 0.35):int(w * 0.65)] = True
        fabric &= alpha > ALPHA_FLOOR

    sel = rgb[fabric]
    if len(sel) == 0:
        sel = rgb.reshape(-1, 3)

    lum = 0.299 * sel[:, 0] + 0.587 * sel[:, 1] + 0.114 * sel[:, 2]
    lo, hi = np.percentile(lum, 35), np.percentile(lum, 85)
    lit = sel[(lum >= lo) & (lum <= hi)]
    if len(lit) == 0:
        lit = sel
    return rgb_to_hex(tuple(np.median(lit, axis=0) / 255.0))
