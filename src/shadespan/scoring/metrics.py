"""Cell scoring: how well does one garment color read against one skin tone?

The score is deterministic and explainable on purpose. Every number in the
report can be traced to a formula in this file; no model opinions, no vibes.

Components (0..100 total):
  visibility   0..45  the stronger of two edge signals, since human vision
                      segments on either: WCAG luminance contrast (full marks
                      at the 4.5:1 AA threshold) or chromatic contrast (a*b*
                      plane distance, full marks at 70, weighted 0.9 because
                      purely chromatic edges are the weaker cue). Cobalt on
                      Fitzpatrick V sits near 1:1 in luminance yet reads
                      clearly; beige on fair skin fails both channels.
  distinction  0..45  CIEDE2000 between garment and skin color, full marks at
                      dE 40. Credits chromatic separation that luminance
                      contrast misses (cobalt on deep skin) while keeping
                      near-skin neutrals (beige on fair, chocolate on deep)
                      down where they belong: failing pairs in the demo
                      catalog measure dE 4..11, passing ones 38..56.
  chroma bonus 0..10  Saturated colors survive low lightness gaps better than
                      muted ones, so chroma buys back a little.

Penalties:
  washout flag        delta L* < WASHOUT_DL and chroma < WASHOUT_CHROMA and
                      hue gap < WASHOUT_HUE. Caps the score at 39 (grade F for
                      that cell) because the failure mode is categorical, not
                      marginal.
  fidelity penalty    optional: dE2000 between catalog hex and the color the
                      VTO actually rendered. Off by default until the sampling
                      region is validated for real renders.

Thresholds are v0 heuristics, set from the CIELAB literature and eyeballing
the demo catalog. They live in one place so a merch team can retune them.
"""
from __future__ import annotations

from ..models import CellScore, Garment, ToneModel
from . import color as C

WASHOUT_DL = 16.0
WASHOUT_CHROMA = 28.0
WASHOUT_HUE = 55.0
CONTRAST_FLOOR = 1.0
CONTRAST_CEIL = 4.5  # WCAG AA text threshold earns full visibility points
DIST_DE_FULL = 40.0  # dE2000 at which distinction maxes out
CHROM_FULL = 70.0    # a*b*-plane distance at which chromatic contrast maxes out
CHROM_WEIGHT = 0.9   # chromatic-only edges are a slightly weaker cue
NEUTRAL_CHROMA = 8.0  # below this, garment hue is noise; washout ignores hue gap
# Studio lighting alone moves a correct render 8-20 dE2000 from its catalog
# swatch, so the drift flag sits above that band. See scoring/fidelity.py.
FIDELITY_WARN_DE = 30.0


def score_cell(
    garment: Garment,
    tone: ToneModel,
    fidelity_delta_e: float | None = None,
    apply_fidelity_penalty: bool = False,
) -> CellScore:
    g_lab = C.hex_to_lab(garment.hex)
    s_lab = C.hex_to_lab(tone.skin_hex)
    g_rgb = C.hex_to_rgb(garment.hex)
    s_rgb = C.hex_to_rgb(tone.skin_hex)

    ratio = C.contrast_ratio(g_rgb, s_rgb)
    d_l = abs(g_lab[0] - s_lab[0])
    hue_gap = C.hue_gap_deg(C.lab_hue_deg(g_lab), C.lab_hue_deg(s_lab))
    chroma = C.lab_chroma(g_lab)
    d_e = C.delta_e2000(g_lab, s_lab)

    # visibility: the stronger of the luminance and chromatic edge signals
    lum_norm = min(1.0, max(0.0, (ratio - CONTRAST_FLOOR) / (CONTRAST_CEIL - CONTRAST_FLOOR)))
    chrom_dist = ((g_lab[1] - s_lab[1]) ** 2 + (g_lab[2] - s_lab[2]) ** 2) ** 0.5
    chrom_norm = CHROM_WEIGHT * min(1.0, chrom_dist / CHROM_FULL)
    vis = 45.0 * max(lum_norm, chrom_norm)

    # distinction: perceptual color difference garment vs skin, into 0..45
    dist = 45.0 * min(1.0, d_e / DIST_DE_FULL)

    bonus = 10.0 * min(chroma / 60.0, 1.0)

    score = vis + dist + bonus
    flags: list[str] = []

    near_neutral = chroma < NEUTRAL_CHROMA  # hue angle is noise for neutrals
    washout = d_l < WASHOUT_DL and chroma < WASHOUT_CHROMA and (hue_gap < WASHOUT_HUE or near_neutral)
    if washout:
        score = min(score, 39.0)
        flags.append(
            f"Washout risk on {tone.label}: garment sits {d_l:.0f} L* from the skin tone "
            f"with muted chroma ({chroma:.0f}) and a {hue_gap:.0f} degree hue gap. It will "
            f"read as skin-colored at the neckline and in listing thumbnails."
        )
    elif ratio < 1.6:
        flags.append(
            f"Low separation on {tone.label}: {ratio:.2f}:1 contrast against the skin tone."
        )

    if fidelity_delta_e is not None and fidelity_delta_e > FIDELITY_WARN_DE:
        flags.append(
            f"Render fidelity: try-on output drifted {fidelity_delta_e:.1f} dE2000 from the "
            f"catalog color on {tone.label}. Check the product photo before trusting this cell."
        )
        if apply_fidelity_penalty:
            score = max(0.0, score - min(20.0, fidelity_delta_e))

    return CellScore(
        garment_sku=garment.sku,
        tone_id=tone.id,
        score=round(min(100.0, max(0.0, score)), 1),
        contrast_ratio=round(ratio, 2),
        delta_l=round(d_l, 1),
        hue_gap_deg=round(hue_gap, 1),
        skin_delta_e=round(d_e, 1),
        garment_chroma=round(chroma, 1),
        washout=washout,
        fidelity_delta_e=None if fidelity_delta_e is None else round(fidelity_delta_e, 1),
        flags=flags,
    )
