"""Gemini text — structured JSON responses for the visual director."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.errors.constants import ERROR_CODE_INTERNAL
from app.errors.exceptions import AppError
from app.integrations.gemini.client import get_gemini_client

log = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def generate_json(prompt: str, *, model: str | None = None) -> dict[str, Any]:
    """Ask Gemini for a JSON document and parse it robustly."""
    client = get_gemini_client()
    model = model or settings.gemini_text_model
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        raw = response.text or ""
    except Exception as exc:
        raise AppError(
            code=ERROR_CODE_INTERNAL,
            message="Gemini text generation failed",
            http_status_code=502,
            details=[str(exc)],
        ) from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = _JSON_BLOCK_RE.search(raw)
        if m:
            return json.loads(m.group(0))
        raise AppError(
            code=ERROR_CODE_INTERNAL,
            message="Gemini returned non-JSON output",
            http_status_code=502,
            details=[raw[:400]],
        ) from None
