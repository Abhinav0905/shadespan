"""Every YouCam path and request body, in one file.

Verified against the live API on 2026-08-16. Two generations coexist and the
shapes differ, so they are spelled out separately rather than unified:

  files      POST /s2s/v1.1/file/{feature}   -> result.files[].file_id + presigned PUT
             PUT  <presigned url>            -> upload the bytes

  cloth      POST /s2s/v2.0/task/cloth       -> data.task_id      (FLAT body)
  (VTO)      GET  /s2s/v2.0/task/cloth/{id}  -> data.task_status + data.results.url

  skin       POST /s2s/v2.0/task/skin-analysis       -> data.task_id  (FLAT body)
  (Skin AI)  GET  /s2s/v2.0/task/skin-analysis/{id}  -> data.task_status + results

Both features are v2.0 and share one shape: a flat body naming file ids
directly, and a task id polled as a PATH segment. The v1.0 generation takes a
nested request_id/payload/actions envelope and polls with ?task_id=, and
mixing the two is the single easiest way to lose an afternoon - v1.0/cloth
accepts a task and then fails it with "invalid_garment_category" no matter
what category you send, because the category never reaches the engine.

Feature slugs confirmed to exist: cloth, skin-analysis, hair-color, makeup,
bag, shoes. There is NO color-analysis endpoint at any version - skin tone
calibration is done by local pixel sampling (`shadespan panel sample`).

If a live call 4xxs, the error body is printed in full and names the offending
field. Fix it here and nowhere else; the orchestrator, scoring and report never
touch these shapes.
"""
from __future__ import annotations

from typing import Any

from ..config import settings


# ---------------------------------------------------------------- files ----
def file_declare_path(feature: str) -> str:
    return f"/s2s/v1.1/file/{feature}"


def file_declare_body(file_name: str, size: int, content_type: str = "image/png") -> dict[str, Any]:
    return {"files": [{"content_type": content_type, "file_name": file_name, "file_size": size}]}


# ------------------------------------------------------------------ VTO ----
# Apparel try-on, API v2.0. src = person photo, ref = garment product photo.
# The body is FLAT (no payload/actions wrapper) and the task id is polled as a
# PATH segment, not a query parameter. Accepted garment_category values,
# brute-forced against the live validator: upper_body, lower_body, full_body,
# auto.

VTO_CATEGORIES = ("upper_body", "lower_body", "full_body", "auto")

# ShadeSpan's catalog vocabulary is richer than the API's. Anything the API
# does not know falls back to "auto" rather than 400-ing the whole cell.
CATEGORY_MAP = {
    "upper_body": "upper_body",
    "lower_body": "lower_body",
    "full_body": "full_body",
    "dresses": "full_body",
}


def vto_task_path() -> str:
    return f"/s2s/v2.0/task/{settings.vto_task}"


def vto_poll_path(task_id: str) -> str:
    return f"/s2s/v2.0/task/{settings.vto_task}/{task_id}"


def vto_task_body(person_file_id: str, garment_file_id: str, category: str) -> dict[str, Any]:
    return {
        "src_file_id": person_file_id,
        "ref_file_id": garment_file_id,
        "garment_category": CATEGORY_MAP.get(category, "auto"),
    }


# ------------------------------------------------------------- accounting --
# Real remaining balance, so a run can report what it actually cost instead of
# trusting a hardcoded units-per-call guess.
CREDIT_PATH = "/s2s/v1.0/client/credit"


# --------------------------------------------------------- skin analysis ---
# API v1.0: nested payload/actions body, task id polled as a query parameter.
# SD and HD concern lists cannot be mixed in one request per the docs.
SKIN_SD_ACTIONS = ["redness", "oiliness", "age_spot", "radiance", "moisture", "dark_circle_v2", "eye_bag", "droopy_upper_eyelid", "firmness", "texture", "acne", "pore", "wrinkle"]


def skin_task_path() -> str:
    return f"/s2s/v2.0/task/{settings.skin_task}"


def skin_poll_path(task_id: str) -> str:
    return f"/s2s/v2.0/task/{settings.skin_task}/{task_id}"


def skin_task_body(src_file_id: str, dst_actions: list[str] | None = None) -> dict[str, Any]:
    return {"src_file_id": src_file_id, "dst_actions": dst_actions or SKIN_SD_ACTIONS}


FEATURES = {
    "vto": settings.vto_task,
    "skin": settings.skin_task,
}
