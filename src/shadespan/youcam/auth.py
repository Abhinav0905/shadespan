"""YouCam (Perfect Corp) S2S authentication.

Flow per the official docs (yce.perfectcorp.com/document, Authentication):
  1. Build the plaintext  "client_id=<API_KEY>&timestamp=<ms_since_epoch>".
  2. RSA-encrypt it with the API *secret*, which is a base64-encoded RSA
     public key, using PKCS#1 v1.5 padding. Base64-encode the ciphertext.
  3. POST {base}/s2s/v1.0/client/auth with {"client_id", "id_token"}.
  4. Use the returned access_token as a Bearer token on every later call.

If Perfect Corp rotates the padding scheme or key format, fix it here and
nowhere else. scripts/smoke_test.py prints the raw auth response so a
mismatch is obvious in seconds.
"""
from __future__ import annotations

import base64
import time

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

from ..config import settings

AUTH_PATH = "/s2s/v1.0/client/auth"


def _load_public_key(secret_b64: str):
    raw = base64.b64decode(secret_b64)
    try:
        return serialization.load_der_public_key(raw)
    except ValueError:
        return serialization.load_pem_public_key(raw)


def make_id_token(api_key: str, secret_b64: str, ts_ms: int | None = None) -> str:
    ts = ts_ms if ts_ms is not None else int(time.time() * 1000)
    plaintext = f"client_id={api_key}&timestamp={ts}".encode()
    pub = _load_public_key(secret_b64)
    ciphertext = pub.encrypt(plaintext, padding.PKCS1v15())
    return base64.b64encode(ciphertext).decode()


class TokenProvider:
    """Fetches and caches the Bearer token; refreshes on demand."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._token: str | None = None

    async def token(self, force: bool = False) -> str:
        if self._token and not force:
            return self._token
        if not settings.youcam_api_key or not settings.youcam_api_secret:
            raise RuntimeError(
                "Live mode needs SHADESPAN_YOUCAM_API_KEY and "
                "SHADESPAN_YOUCAM_API_SECRET (see .env.example)."
            )
        resp = await self._client.post(
            settings.youcam_base_url + AUTH_PATH,
            json={
                "client_id": settings.youcam_api_key,
                "id_token": make_id_token(settings.youcam_api_key, settings.youcam_api_secret),
            },
        )
        body = resp.json()
        token = (body.get("result") or {}).get("access_token")
        if resp.status_code != 200 or not token:
            raise RuntimeError(f"YouCam auth failed ({resp.status_code}): {body}")
        self._token = token
        return token
