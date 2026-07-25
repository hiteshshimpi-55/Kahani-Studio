"""Gemini API client (text director + Nano Banana images)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.errors.constants import ERROR_CODE_INTERNAL
from app.errors.exceptions import AppError


@lru_cache(maxsize=1)
def get_gemini_client() -> Any:
    try:
        from google import genai
    except ImportError as exc:
        raise AppError(
            code=ERROR_CODE_INTERNAL,
            message="google-genai package is not installed",
            http_status_code=503,
            details=["Install google-genai to enable Gemini integrations"],
        ) from exc

    key = (settings.gemini_api_key or "").strip()
    if not key:
        raise AppError(
            code=ERROR_CODE_INTERNAL,
            message="GEMINI_API_KEY is not set",
            http_status_code=503,
            details=["Set GEMINI_API_KEY in .env to enable visual generation"],
        )
    return genai.Client(api_key=key)
