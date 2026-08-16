"""Color math used by the scoring engine.

Implements sRGB -> CIELAB (D65), CIEDE2000, WCAG relative-luminance contrast
and the Individual Typology Angle (ITA) used in dermatology to band skin
tones. Pure functions, no dependencies beyond math, unit-tested against
published reference values.
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------- sRGB / XYZ


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        raise ValueError(f"expected #RRGGBB, got {hex_color!r}")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{round(max(0.0, min(1.0, c)) * 255):02X}" for c in rgb)


def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb1: tuple[float, float, float], rgb2: tuple[float, float, float]) -> float:
    """WCAG contrast ratio, 1.0 (identical) .. 21.0 (black on white)."""
    l1, l2 = relative_luminance(rgb1), relative_luminance(rgb2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# D65 reference white
_XN, _YN, _ZN = 0.95047, 1.0, 1.08883


def rgb_to_xyz(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    return x, y, z


def _f(t: float) -> float:
    return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)


def rgb_to_lab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = rgb_to_xyz(rgb)
    fx, fy, fz = _f(x / _XN), _f(y / _YN), _f(z / _ZN)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def hex_to_lab(hex_color: str) -> tuple[float, float, float]:
    return rgb_to_lab(hex_to_rgb(hex_color))


def lab_chroma(lab: tuple[float, float, float]) -> float:
    _, a, b = lab
    return math.hypot(a, b)


def lab_hue_deg(lab: tuple[float, float, float]) -> float:
    _, a, b = lab
    return math.degrees(math.atan2(b, a)) % 360.0


def hue_gap_deg(h1: float, h2: float) -> float:
    d = abs(h1 - h2) % 360.0
    return min(d, 360.0 - d)


# --------------------------------------------------------------------- ITA


def ita_deg(lab: tuple[float, float, float]) -> float:
    """Individual Typology Angle. Standard dermatology banding:
    >55 very light, 41..55 light, 28..41 intermediate, 10..28 tan,
    -30..10 brown, <-30 dark."""
    l, _, b = lab
    if b == 0:
        b = 1e-6
    return math.degrees(math.atan((l - 50.0) / b))


def ita_band(ita: float) -> str:
    if ita > 55:
        return "very light"
    if ita > 41:
        return "light"
    if ita > 28:
        return "intermediate"
    if ita > 10:
        return "tan"
    if ita > -30:
        return "brown"
    return "dark"


# ---------------------------------------------------------------- CIEDE2000


def delta_e2000(
    lab1: tuple[float, float, float], lab2: tuple[float, float, float]
) -> float:
    """CIEDE2000 color difference (Sharma et al. 2005 formulation)."""
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2

    c1 = math.hypot(a1, b1)
    c2 = math.hypot(a2, b2)
    c_bar = (c1 + c2) / 2.0
    g = 0.5 * (1 - math.sqrt(c_bar**7 / (c_bar**7 + 25.0**7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)

    def hp(ap: float, b: float) -> float:
        if ap == 0 and b == 0:
            return 0.0
        h = math.degrees(math.atan2(b, ap))
        return h + 360.0 if h < 0 else h

    h1p, h2p = hp(a1p, b1), hp(a2p, b2)

    dlp = l2 - l1
    dcp = c2p - c1p

    if c1p * c2p == 0:
        dhp_deg = 0.0
    else:
        dh = h2p - h1p
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
        dhp_deg = dh
    dhp = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dhp_deg) / 2.0)

    lbp = (l1 + l2) / 2.0
    cbp = (c1p + c2p) / 2.0

    if c1p * c2p == 0:
        hbp = h1p + h2p
    else:
        hsum = h1p + h2p
        if abs(h1p - h2p) <= 180:
            hbp = hsum / 2.0
        elif hsum < 360:
            hbp = (hsum + 360) / 2.0
        else:
            hbp = (hsum - 360) / 2.0

    t = (
        1
        - 0.17 * math.cos(math.radians(hbp - 30))
        + 0.24 * math.cos(math.radians(2 * hbp))
        + 0.32 * math.cos(math.radians(3 * hbp + 6))
        - 0.20 * math.cos(math.radians(4 * hbp - 63))
    )
    d_theta = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    rc = 2 * math.sqrt(cbp**7 / (cbp**7 + 25.0**7))
    sl = 1 + (0.015 * (lbp - 50) ** 2) / math.sqrt(20 + (lbp - 50) ** 2)
    sc = 1 + 0.045 * cbp
    sh = 1 + 0.015 * cbp * t
    rt = -math.sin(math.radians(2 * d_theta)) * rc

    return math.sqrt(
        (dlp / sl) ** 2
        + (dcp / sc) ** 2
        + (dhp / sh) ** 2
        + rt * (dcp / sc) * (dhp / sh)
    )
