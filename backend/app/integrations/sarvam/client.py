from __future__ import annotations

import functools

from sarvamai import SarvamAI

from app.core.config import settings


@functools.lru_cache(maxsize=1)
def get_sarvam_client() -> SarvamAI:
    key = settings.sarvam_api_key
    if not key:
        raise RuntimeError("SARVAM_API_KEY is not set")
    return SarvamAI(api_subscription_key=key)
