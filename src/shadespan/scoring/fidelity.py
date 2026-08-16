"""Did the try-on actually render the colour we asked for?

The audit's scores come from calibrated colour (catalog hex vs skin hex). The
renders sit beside them as visual evidence, and evidence that contradicts the
score is worse than no evidence at all: a cell can confidently report "this
blush tee disappears on Fitzpatrick I" while showing a photo of a black shirt,
because the VTO quietly returned the model's original clothing instead.

So we measure the render: sample the fabric on the chest and compare it to the
catalog swatch in dE2000. See rendered_garment_hex for why that takes both a
diff against the source photo and a torso window, rather than either alone.

This is a heuristic, and it is honest about being one. Checked by eye against
14 cells of a live run it agreed on 10. It misses when the source photo is a
landscape crop (the torso window drifts off the chest) and over-reports on
pale garments over deep skin (shadowed fabric measures far darker than its
swatch). Studio lighting alone moves a correct render 8-20 dE, which is why
FIDELITY_DRIFT_DE sits well above that band.

So drift is reported, never scored: it adds a "check this render" flag and
leaves the cell's score untouched. A flag a merchandiser can dismiss in a
second is worth having at this accuracy; a penalty built on a lighting
artefact would quietly corrupt the grade. Folding this into the score needs
real garment segmentation, not a box.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .color import delta_e2000, hex_to_lab, rgb_to_hex

# Pixels must differ by this much (sum over RGB) to count as "the try-on
# touched this". Below it, JPEG noise and re-encoding dominate.
CHANGED_PIXEL_THRESHOLD = 60

# Fewer changed pixels than this and there is no garment to measure: the
# try-on effectively did nothing.
MIN_CHANGED_PIXELS = 2000

# dE2000 between catalog swatch and rendered fabric above which the render is
# not showing the requested colour. Deliberately generous: studio lighting
# alone moves a correct render 8-20 dE.
FIDELITY_DRIFT_DE = 30.0


# The chest: horizontally central, below the neckline, above the crop edge.
# Fractions of image width/height, so a landscape source crops the same way.
TORSO_BOX = (0.38, 0.55, 0.62, 0.95)


def rendered_garment_hex(render: Path, source: Path) -> tuple[str | None, int]:
    """Median colour of the fabric the try-on painted on the chest.

    Returns (hex, garment_pixel_count). hex is None when there is too little
    garment in the torso window to measure.

    Two constraints together, because neither alone is enough. The changed
    mask says where the try-on acted, but on its own it also catches repainted
    skin, hair and collar edges - and when the original garment and the new one
    are both dark, the only pixels that clear the change threshold ARE those
    edges, so a correct charcoal render measures light grey. The torso window
    says where fabric must be, but on its own it catches whatever the engine
    left behind if the try-on silently failed. Intersecting them measures
    fabric the try-on actually painted.
    """
    r = Image.open(render).convert("RGB")
    s = Image.open(source).convert("RGB")
    if r.size != s.size:
        s = s.resize(r.size)
    R = np.asarray(r).astype(float)
    S = np.asarray(s).astype(float)
    h, w = R.shape[:2]

    changed = np.abs(R - S).sum(axis=2) > CHANGED_PIXEL_THRESHOLD
    box = np.zeros_like(changed)
    x0, y0, x1, y1 = TORSO_BOX
    box[int(h * y0):int(h * y1), int(w * x0):int(w * x1)] = True

    mask = changed & box
    # Dark-on-dark swaps barely move any pixel; fall back to the torso window
    # alone rather than measuring collar edges.
    if int(mask.sum()) < MIN_CHANGED_PIXELS:
        mask = box
    n = int(mask.sum())
    if n < MIN_CHANGED_PIXELS:
        return None, n

    sel = R[mask]
    lum = 0.299 * sel[:, 0] + 0.587 * sel[:, 1] + 0.114 * sel[:, 2]
    lo, hi = np.percentile(lum, 25), np.percentile(lum, 75)
    band = sel[(lum >= lo) & (lum <= hi)]
    if len(band) == 0:
        band = sel
    return rgb_to_hex(tuple(np.median(band, axis=0) / 255.0)), n


def render_drift(render: Path, source: Path, catalog_hex: str) -> tuple[float | None, str | None]:
    """(dE2000 from the catalog colour, rendered hex). (None, None) if unmeasurable."""
    hexv, _ = rendered_garment_hex(render, source)
    if hexv is None:
        return None, None
    return delta_e2000(hex_to_lab(catalog_hex), hex_to_lab(hexv)), hexv
