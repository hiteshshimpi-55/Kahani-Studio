"""Gemini integrations — lazy exports so missing google-genai does not block API boot."""

from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    if name == "get_gemini_client":
        from app.integrations.gemini.client import get_gemini_client

        return get_gemini_client
    if name == "generate_image":
        from app.integrations.gemini.images import generate_image

        return generate_image
    if name == "generate_json":
        from app.integrations.gemini.text import generate_json

        return generate_json
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["get_gemini_client", "generate_image", "generate_json"]
