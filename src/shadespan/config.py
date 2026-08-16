"""Runtime configuration.

Everything sensitive or environment-specific comes from env vars (see
.env.example). Nothing here is required for mock mode.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHADESPAN_", env_file=".env", extra="ignore")

    # --- YouCam API credentials (live mode only) ---
    youcam_api_key: str = ""
    youcam_api_secret: str = ""  # base64 RSA public key from the API console
    youcam_base_url: str = "https://yce-api-01.perfectcorp.com"

    # --- Feature slugs, verified against the live API on 2026-08-16. All
    # endpoint paths are derived from these in youcam/endpoints.py. Slugs
    # confirmed to exist: cloth, skin-analysis, hair-color, makeup, bag, shoes.
    vto_task: str = "cloth"
    skin_task: str = "skin-analysis"

    # --- Unit accounting. Measured against the live account on 2026-08-16:
    # 12 cloth renders moved the balance from 1036 to 1012, i.e. 2 units each.
    # `shadespan credit` reads the real balance if you want to re-verify.
    units_per_vto: int = 2
    units_per_analysis: int = 7
    max_units_per_run: int = 400

    # --- TLS ---
    # Corporate networks that inspect HTTPS present their own root, which is
    # not in certifi's store, so every live call dies with
    # CERTIFICATE_VERIFY_FAILED. Point this at a PEM holding certifi's roots
    # *plus* your company root; `make ca-bundle` builds one. Empty means use
    # the default trust store, which is right on an unmanaged machine.
    ca_bundle: str = ""

    # --- Public deployment guard ---
    # A hosted dashboard spends the account's units on behalf of strangers.
    # Once this many units have gone on try-ons in one process, live mode
    # stops being offered and the mock engine serves everyone: the page keeps
    # working and demonstrating the idea, it just stops costing money. 0
    # disables the guard, which is what you want locally.
    public_unit_budget: int = 0

    # --- Orchestration ---
    concurrency: int = 3
    poll_interval_s: float = 2.0
    poll_timeout_s: float = 180.0
    http_timeout_s: float = 60.0

    runs_dir: str = "runs"


settings = Settings()
