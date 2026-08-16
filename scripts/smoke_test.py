"""Live smoke test. Run this BEFORE any real audit.

  python scripts/smoke_test.py path/to/model_photo.jpg [path/to/garment.png]

It does, in order, printing every raw response:
  1. auth                      proves your key/secret and the RSA padding
  2. file declare + upload     proves the presigned-PUT flow
  3. apparel VTO task          proves the try-on payload shape
  4. skin analysis task        proves the Skin AI payload shape
  5. color analysis task       optional; comment in when you use it

Anything that 4xxs prints the API's own error body. Compare that against the
feature page at https://yce.perfectcorp.com/document, fix the field name in
src/shadespan/youcam/endpoints.py, rerun. Budget: one run of this script
costs roughly units_per_vto + units_per_analysis (see console pricing).
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shadespan.config import settings  # noqa: E402
from shadespan.youcam.client import YouCamClient  # noqa: E402


async def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    person = Path(sys.argv[1])
    garment = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        Path(__file__).resolve().parents[1] / "assets" / "catalog" / "tee-cobalt.png")

    print(f"base url : {settings.youcam_base_url}")
    print(f"vto task : {settings.vto_task} | skin task: {settings.skin_task}")
    client = YouCamClient()
    try:
        print("\n[1] auth …")
        token = await client._tokens.token()
        print(f"    ok, token starts {token[:12]}…")

        print("\n[2+3] apparel VTO …")
        img, task_id = await client.try_on(person, garment, "upper_body")
        out = Path("smoke_vto.png")
        out.write_bytes(img)
        print(f"    ok, task {task_id}, wrote {out} ({len(img)//1024} KB)")

        print("\n[4] skin analysis …")
        result = await client.skin_analysis(person)
        print("    ok:", json.dumps(result)[:600])

        # print("\n[5] color analysis …")
        # print(json.dumps(await client.color_analysis(person))[:600])

        print("\nAll green. You are clear to run:  shadespan audit --live")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
