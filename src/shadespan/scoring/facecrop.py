"""Find the face in a catalog-style photo and crop to it.

YouCam Skin AI rejects an image whose face is small relative to the frame with
"error_src_face_too_small", and every photo in a try-on panel is framed for the
garment, not the face - head-and-shoulders at best, full body at worst. Raising
the resolution does not help, because the constraint is the face-to-frame
ratio, not pixel count: the same photo fails at 1000px and at 2400px.

There is no face detector in the dependency set and adding one for a crop would
be heavy, so the face is located the same way skin tone is sampled: skin-toned
pixels in the upper half of the frame, whose centroid is the face and whose
spread sets the crop radius. That is enough for portrait and half-body sources.
It would not survive a busy background full of skin-toned wall, which is why
the caller treats a rejected crop as a per-member warning rather than a failure.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

# Crop this many times the detected skin spread, so the result holds the whole
# head plus a margin rather than a tight box on the cheeks.
FACE_MARGIN = 1.9

# Skin AI wants a reasonably large face; upscale small crops to meet it.
MIN_CROP_PX = 1000


def face_box(img: Image.Image, margin: float = FACE_MARGIN) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) around the face, in pixel coordinates."""
    w, h = img.size
    upper = img.crop((0, 0, w, int(h * 0.6)))
    a = np.asarray(upper.convert("RGB")).astype(float)
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    Y = 0.299 * R + 0.587 * G + 0.114 * B
    Cr = (R - Y) * 0.713 + 128
    Cb = (B - Y) * 0.564 + 128
    mask = (Cr > 133) & (Cr < 177) & (Cb > 77) & (Cb < 127) & (R > G + 8) & (G > B) & (R > 30)

    ys, xs = np.nonzero(mask)
    if len(xs) < 500:  # no confident skin: fall back to the usual portrait crop
        side = int(min(w, h * 0.45))
        cx = w // 2
        return max(0, cx - side // 2), 0, min(w, cx + side // 2), min(h, side)

    cx, cy = float(xs.mean()), float(ys.mean())
    spread = max(float(xs.std()), float(ys.std()), 20.0)
    half = spread * margin
    return (max(0, int(cx - half)), max(0, int(cy - half)),
            min(w, int(cx + half)), min(h, int(cy + half)))


# Loose first, because a crop that clips the jaw or forehead also fails
# detection; tighten only when the API says the face is too small. Long hair,
# bare shoulders and a wide smile all leave less face per frame at any given
# margin, so the retry ladder matters more than the starting value.
CROP_LADDER = (FACE_MARGIN, 1.45, 1.15, None)


def centered_box(img: Image.Image) -> tuple[int, int, int, int]:
    """Head-and-shoulders box assuming a conventionally framed portrait.

    The skin-mask centroid fails when hair reads as skin - warm auburn against
    a warm wall is indistinguishable from a cheek by chroma alone - and a
    mis-centred box cannot be rescued by resizing it: tightening walks it
    further off the face until the API reports the face out of bounds rather
    than too small. Geometry is the fallback when colour has misled us.
    """
    w, h = img.size
    side = int(min(w * 0.6, h * 0.5))
    cx = w // 2
    top = int(h * 0.04)
    return max(0, cx - side // 2), top, min(w, cx + side // 2), min(h, top + side)


def write_face_crop(source: Path, dest: Path, margin: float | None = FACE_MARGIN) -> Path:
    """Crop `source` to its face and write it to `dest`. Returns `dest`.

    `margin=None` selects the geometric fallback instead of skin detection.
    """
    img = Image.open(source).convert("RGB")
    crop = img.crop(centered_box(img) if margin is None else face_box(img, margin))
    if min(crop.size) < MIN_CROP_PX:
        scale = MIN_CROP_PX / min(crop.size)
        crop = crop.resize((int(crop.width * scale), int(crop.height * scale)), Image.LANCZOS)
    crop.save(dest, quality=92)
    return dest
