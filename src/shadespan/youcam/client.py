"""Async client for the YouCam S2S API.

One public method per pipeline need. All HTTP details, retries and polling
live here; callers get bytes in, bytes out.
"""
from __future__ import annotations

import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from ..config import settings
from . import endpoints as ep
from .auth import TokenProvider

log = logging.getLogger("shadespan.youcam")


class YouCamError(RuntimeError):
    pass


def _retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (429, 500, 502, 503, 504)


class YouCamClient:
    """Real client. Construct once, share across the run."""

    name = "youcam-live"

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=settings.http_timeout_s)
        self._tokens = TokenProvider(self._http)
        self._file_cache: dict[str, str] = {}  # sha of path+mtime -> file_id

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {await self._tokens.token()}"}

    @retry(retry=retry_if_exception(_retryable), stop=stop_after_attempt(4), wait=wait_exponential(min=1, max=15), reraise=True)
    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        r = await self._http.post(settings.youcam_base_url + path, json=body, headers=await self._headers())
        if r.status_code == 401:
            await self._tokens.token(force=True)
            r = await self._http.post(settings.youcam_base_url + path, json=body, headers=await self._headers())
        if r.status_code >= 400:
            log.error("POST %s -> %s %s", path, r.status_code, r.text[:800])
            r.raise_for_status()
        return r.json()

    @retry(retry=retry_if_exception(_retryable), stop=stop_after_attempt(4), wait=wait_exponential(min=1, max=15), reraise=True)
    async def _get(self, path: str) -> dict[str, Any]:
        r = await self._http.get(settings.youcam_base_url + path, headers=await self._headers())
        if r.status_code >= 400:
            log.error("GET %s -> %s %s", path, r.status_code, r.text[:800])
            r.raise_for_status()
        return r.json()

    # ---------------------------------------------------------------- files
    async def upload_image(self, path: Path, feature: str) -> str:
        """Declare + upload one image, return its file_id. Cached per path."""
        key = f"{feature}:{path.resolve()}:{path.stat().st_mtime_ns}"
        if key in self._file_cache:
            return self._file_cache[key]
        data = path.read_bytes()
        ctype = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        body = await self._post(ep.file_declare_path(feature), ep.file_declare_body(path.name, len(data), ctype))
        try:
            fentry = body["result"]["files"][0]
            file_id = fentry["file_id"]
            req = (fentry.get("requests") or [{}])[0]
            put_url, put_headers = req["url"], req.get("headers") or {}
        except (KeyError, IndexError) as exc:
            raise YouCamError(f"unexpected file-declare response: {body}") from exc
        put = await self._http.put(put_url, content=data, headers={**put_headers, "Content-Type": ctype})
        if put.status_code >= 400:
            raise YouCamError(f"upload PUT failed {put.status_code}: {put.text[:400]}")
        self._file_cache[key] = file_id
        return file_id

    # ---------------------------------------------------------------- tasks
    @staticmethod
    def _envelope(body: dict[str, Any]) -> dict[str, Any]:
        """v2.0 replies under "data", v1.0 under "result". Same meaning."""
        return body.get("data") or body.get("result") or {}

    async def _run_task(self, create_path: str, poll_path, body: dict[str, Any],
                        label: str) -> dict[str, Any]:
        """Create a task, poll to completion, return its envelope.

        poll_path is a callable task_id -> path, because v2.0 puts the id in
        the path and v1.0 in the query string.
        """
        created = self._envelope(await self._post(create_path, body))
        task_id = created.get("task_id")
        if not task_id:
            raise YouCamError(f"no task_id in {label} response: {created}")
        deadline = asyncio.get_event_loop().time() + settings.poll_timeout_s
        while True:
            state = self._envelope(await self._get(poll_path(task_id)))
            status = (state.get("task_status") or state.get("polling_status")
                      or state.get("status") or "").lower()
            if status in ("success", "succeeded", "done"):
                state["task_id"] = task_id
                return state
            if status in ("error", "failed"):
                raise YouCamError(
                    f"{label} task failed: {state.get('error_message') or state.get('error') or state}")
            if asyncio.get_event_loop().time() > deadline:
                raise YouCamError(f"{label} task {task_id} timed out after {settings.poll_timeout_s}s")
            await asyncio.sleep(settings.poll_interval_s)

    @staticmethod
    def _first_url(state: dict[str, Any]) -> str:
        """Dig the first output url out of a polling envelope.

        v2.0 cloth returns results as a single object; v1.0 features return a
        list of results each holding a data list. Both shapes handled.
        """
        results = state.get("results")
        if isinstance(results, dict):
            if results.get("url"):
                return results["url"]
            results = [results]
        for res in results or []:
            for d in res.get("data", []) or []:
                if d.get("url"):
                    return d["url"]
            if res.get("url"):
                return res["url"]
        if state.get("url"):
            return state["url"]
        raise YouCamError(f"no output url in task result: {state}")

    async def _download(self, url: str) -> bytes:
        r = await self._http.get(url)
        r.raise_for_status()
        return r.content

    # ----------------------------------------------------------- public api
    async def credit_balance(self) -> float:
        """Units actually left on the account, summed across credit grants."""
        body = await self._get(ep.CREDIT_PATH)
        return sum(float(r.get("amount_dec") or r.get("amount") or 0)
                   for r in body.get("results") or [])

    async def try_on(self, person: Path, garment: Path, category: str) -> tuple[bytes, str]:
        """Render garment on person. Returns (image bytes, task_id)."""
        feature = ep.FEATURES["vto"]
        person_id = await self.upload_image(person, feature)
        garment_id = await self.upload_image(garment, feature)
        state = await self._run_task(
            ep.vto_task_path(), ep.vto_poll_path,
            ep.vto_task_body(person_id, garment_id, category), "cloth")
        return await self._download(self._first_url(state)), state["task_id"]

    async def skin_analysis(self, person: Path) -> dict[str, Any]:
        fid = await self.upload_image(person, ep.FEATURES["skin"])
        return await self._run_task(
            ep.skin_task_path(), ep.skin_poll_path, ep.skin_task_body(fid), "skin-analysis")

    async def skin_analysis_scores(self, person: Path) -> dict[str, Any]:
        """Per-concern Skin AI scores for one photo.

        The feature rejects anything where the face does not fill enough of the
        frame ("error_src_face_too_small"), and a full-body catalog shot never
        does, so the face is cropped out first. Results come back as a zip of
        per-concern masks plus one json of scores; only the scores are kept.
        """
        import io
        import zipfile

        from ..scoring.facecrop import CROP_LADDER, write_face_crop

        with tempfile.TemporaryDirectory() as tmp:
            last: Exception | None = None
            for margin in CROP_LADDER:
                crop = write_face_crop(person, Path(tmp) / "face.jpg", margin)
                try:
                    state = await self.skin_analysis(crop)
                except YouCamError as exc:
                    if not any(k in str(exc) for k in ("face_too_small", "face_out_of_bound")):
                        raise
                    log.info("skin-analysis: %s rejected at margin %s, retrying", person.name, margin)
                    last = exc
                    continue
                url = self._first_url(state)
                blob = zipfile.ZipFile(io.BytesIO(await self._download(url)))
                for name in blob.namelist():
                    if name.endswith(".json"):
                        raw = json.loads(blob.read(name).decode())
                        return {k: v.get("ui_score") for k, v in raw.items()
                                if isinstance(v, dict) and "ui_score" in v}
                raise YouCamError(f"no score json in skin-analysis result for {person.name}")
            raise last or YouCamError(f"skin-analysis failed for {person.name}")
