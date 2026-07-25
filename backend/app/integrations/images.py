"""Unified image generation — OpenAI GPT Image (default) or Gemini Nano Banana."""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings

log = logging.getLogger(__name__)


def normalize_image_provider(value: str | None) -> str:
    """Map API aliases to internal provider ids. Default: openai (ChatGPT)."""
    raw = (value or settings.image_provider or "openai").strip().lower()
    if raw in ("chatgpt", "openai", "gpt", "gpt-image", "gpt-image-1", "dall-e"):
        return "openai"
    if raw in ("gemini", "nano-banana", "google"):
        return "gemini"
    return "openai"


def generate_image(
    prompt: str,
    *,
    reference_image_paths: list[str] | None = None,
    dest: Path,
    aspect_ratio: str = "9:16",
    image_provider: str | None = None,
) -> Path:
    """Route to IMAGE_PROVIDER (openai | gemini), with cross-fallback.

    ``image_provider`` overrides settings for this call (per-request API option).
    """
    provider = normalize_image_provider(image_provider)
    order = [provider]
    other = "gemini" if provider == "openai" else "openai"
    order.append(other)

    last_error: Exception | None = None
    for name in order:
        try:
            if name == "openai":
                from app.integrations.openai_images import generate_image_openai

                return generate_image_openai(
                    prompt,
                    reference_image_paths=reference_image_paths,
                    dest=dest,
                    aspect_ratio=aspect_ratio,
                )
            from app.integrations.gemini.images import generate_image as gemini_generate

            return gemini_generate(
                prompt,
                reference_image_paths=reference_image_paths,
                dest=dest,
                aspect_ratio=aspect_ratio,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            log.warning("image_provider_failed provider=%s err=%s", name, exc)

    raise last_error or RuntimeError("image generation failed")
