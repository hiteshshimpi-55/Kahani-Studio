"""Nano Banana image generation with character reference images.

Character consistency technique (per Gemini docs):
- Pass locked character sheets as reference images alongside the prompt.
- Refer to them explicitly: "the man from image 1", "the woman from image 2".
- Describe wardrobe with concrete detail to prevent drift.
"""

from __future__ import annotations

import logging
from pathlib import Path

from google.genai import types

from app.core.config import settings
from app.errors.constants import ERROR_CODE_INTERNAL
from app.errors.exceptions import AppError
from app.integrations.gemini.client import get_gemini_client

log = logging.getLogger(__name__)


def _guess_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "image/png")


def generate_image(
    prompt: str,
    *,
    reference_image_paths: list[str] | None = None,
    dest: Path,
    aspect_ratio: str = "9:16",
) -> Path:
    """Generate one image; optionally condition on reference images.

    Tries the configured model first, then the fallback (accounts may
    not have access to the newest Nano Banana release).
    """
    client = get_gemini_client()
    parts: list[types.Part] = []
    for ref in reference_image_paths or []:
        p = Path(ref)
        parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=_guess_mime(p)))
    parts.append(types.Part.from_text(text=prompt))

    last_error: Exception | None = None
    for model in (settings.gemini_image_model, settings.gemini_image_fallback_model):
        try:
            response = client.models.generate_content(
                model=model,
                contents=types.Content(role="user", parts=parts),
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )
            for candidate in response.candidates or []:
                for part in (candidate.content.parts if candidate.content else []) or []:
                    if part.inline_data and part.inline_data.data:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(part.inline_data.data)
                        log.info(
                            "gemini_image_ok model=%s dest=%s bytes=%d refs=%d",
                            model, dest.name, len(part.inline_data.data),
                            len(reference_image_paths or []),
                        )
                        return dest
            last_error = RuntimeError(f"no image in response from {model}")
            log.warning("gemini_image_empty model=%s — trying fallback", model)
        except Exception as exc:  # noqa: BLE001 — try fallback model
            last_error = exc
            log.warning("gemini_image_failed model=%s err=%s — trying fallback", model, exc)

    raise AppError(
        code=ERROR_CODE_INTERNAL,
        message="Gemini image generation failed",
        http_status_code=502,
        details=[str(last_error), prompt[:200]],
    )
