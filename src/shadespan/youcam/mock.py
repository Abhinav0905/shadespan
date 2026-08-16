"""Offline stand-in for the YouCam client.

Renders a flat-illustration try-on locally: the panel figure with the garment
silhouette recolored to the catalog hex, shaded, and watermarked MOCK so it
can never be mistaken for a real VTO output. The whole pipeline, scoring
engine, report and dashboard run against this with zero API units, which is
how you develop, test and demo without touching the 1,000-unit budget.

Interface matches YouCamClient exactly.
"""
from __future__ import annotations

import asyncio
import io
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter


def _hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _shade(rgb: tuple[int, int, int], k: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, round(c * k))) for c in rgb)  # type: ignore[return-value]


class MockYouCamClient:
    name = "mock"

    def __init__(self, garment_hexes: dict[str, str], panel_hexes: dict[str, str]):
        """Both maps key by file path name so the mock can look colors up the
        same way the real API sees files."""
        self._garment_hexes = garment_hexes
        self._panel_hexes = panel_hexes

    async def aclose(self) -> None:  # symmetry with the real client
        return None

    async def try_on(self, person: Path, garment: Path, category: str) -> tuple[bytes, str]:
        await asyncio.sleep(0.02)  # keep the orchestrator honest about async
        skin = _hex_rgb(self._panel_hexes.get(person.name, "#D9A579"))
        cloth = _hex_rgb(self._garment_hexes.get(garment.name, "#888888"))

        w, h = 640, 854
        img = Image.new("RGB", (w, h), (241, 240, 237))
        d = ImageDraw.Draw(img)
        d.rectangle([0, int(h * 0.64), w, h], fill=(230, 228, 223))
        cx = w // 2

        d.rounded_rectangle([cx - 27, 208, cx + 27, 266], 14, fill=_shade(skin, 0.94))  # neck
        d.ellipse([cx - 74, 78, cx + 74, 238], fill=skin)  # head
        d.ellipse([cx - 33, 138, cx - 19, 155], fill=_shade(skin, 0.7))
        d.ellipse([cx + 19, 138, cx + 33, 155], fill=_shade(skin, 0.7))
        d.rounded_rectangle([cx - 165, 268, cx - 109, 580], 27, fill=skin)  # arms
        d.rounded_rectangle([cx + 109, 268, cx + 165, 580], 27, fill=skin)

        if category == "dresses":
            body = [(cx - 66, 252), (cx + 66, 252), (cx + 118, 336), (cx + 96, 372),
                    (cx + 150, 700), (cx - 150, 700), (cx - 96, 372), (cx - 118, 336)]
        else:
            body = [(cx - 66, 252), (cx + 66, 252), (cx + 126, 336), (cx + 102, 380),
                    (cx + 118, 620), (cx - 118, 620), (cx - 102, 380), (cx - 126, 336)]
        d.polygon(body, fill=cloth)
        d.arc([cx - 44, 236, cx + 44, 284], 0, 180, fill=_shade(cloth, 0.8), width=8)
        rng = random.Random(garment.name + person.name)
        for _ in range(3):  # fold hints
            fx = cx + rng.randint(-70, 70)
            d.line([(fx, 320), (fx + rng.randint(-14, 14), 600 if category != "dresses" else 690)],
                   fill=_shade(cloth, 0.88), width=3)

        img = img.filter(ImageFilter.GaussianBlur(0.4))
        d = ImageDraw.Draw(img)
        d.text((16, h - 30), "MOCK RENDER - not a YouCam output", fill=(140, 138, 133))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), f"mock-{garment.stem}-{person.stem}"

    async def skin_analysis(self, person: Path) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"task_id": f"mock-skin-{person.stem}", "results": [], "mock": True}

    async def color_analysis(self, person: Path) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        hexc = self._panel_hexes.get(person.name, "#D9A579")
        return {"task_id": f"mock-color-{person.stem}", "skin_tone": hexc, "mock": True}
