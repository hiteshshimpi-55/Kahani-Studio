"""OpenAI GPT Image generation with character reference images.

Uses images.generate for lookbook sheets (no refs) and images.edit when
character reference sheets are attached — same identity technique as Gemini.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

from openai import OpenAI

from app.core.config import settings
from app.errors.constants import ERROR_CODE_INTERNAL
from app.errors.exceptions import AppError

log = logging.getLogger(__name__)

_ASPECT_TO_SIZE = {
    "1:1": "1024x1024",
    "16:9": "1536x1024",
    "9:16": "1024x1536",
    "3:4": "1024x1536",
    "4:3": "1536x1024",
}


def _client() -> OpenAI:
    key = (settings.llm_api_key or settings.openai_api_key or "").strip()
    if not key:
        raise AppError(
            code=ERROR_CODE_INTERNAL,
            message="LLM_API_KEY / OPENAI_API_KEY is not set",
            http_status_code=503,
            details=["Set LLM_API_KEY in .env to use OpenAI image generation"],
        )
    return OpenAI(api_key=key)


def _write_b64(dest: Path, b64: str) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(base64.b64decode(b64))
    return dest


def generate_image_openai(
    prompt: str,
    *,
    reference_image_paths: list[str] | None = None,
    dest: Path,
    aspect_ratio: str = "9:16",
) -> Path:
    """Generate one image via GPT Image; optional refs via images.edit."""
    client = _client()
    size = _ASPECT_TO_SIZE.get(aspect_ratio, "1024x1536")
    quality = (settings.openai_image_quality or "medium").strip()
    models: list[str] = []
    for m in (
        settings.openai_image_model,
        settings.openai_image_fallback_model,
        "gpt-image-1",
        "dall-e-3",
    ):
        if m and m not in models:
            models.append(m)

    refs = [Path(p) for p in (reference_image_paths or []) if Path(p).exists()]
    last_error: Exception | None = None

    for model in models:
        try:
            if refs and not model.startswith("dall-e"):
                files = [open(p, "rb") for p in refs]
                try:
                    kwargs: dict = {
                        "model": model,
                        "image": files if len(files) > 1 else files[0],
                        "prompt": (
                            prompt
                            + " Preserve the exact face, hair, body shape, and wardrobe "
                            "identity from each reference image. Reference image order "
                            "matches characters named in the prompt."
                        ),
                        "size": size,
                        "quality": quality,
                    }
                    if model.startswith("gpt-image-1") and model != "gpt-image-2":
                        kwargs["input_fidelity"] = "high"
                    result = client.images.edit(**kwargs)
                finally:
                    for f in files:
                        f.close()
            else:
                gen_kwargs: dict = {
                    "model": model,
                    "prompt": prompt,
                    "n": 1,
                }
                if model.startswith("gpt-image"):
                    gen_kwargs["size"] = size
                    gen_kwargs["quality"] = quality
                else:
                    gen_kwargs["size"] = (
                        "1024x1792" if aspect_ratio in ("9:16", "3:4") else "1024x1024"
                    )
                    gen_kwargs["quality"] = "standard"
                    gen_kwargs["response_format"] = "b64_json"
                result = client.images.generate(**gen_kwargs)

            item = (result.data or [None])[0]
            if item is None:
                raise RuntimeError(f"empty image response from {model}")
            b64 = getattr(item, "b64_json", None)
            if not b64 and getattr(item, "url", None):
                import urllib.request

                dest.parent.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(item.url, dest)  # noqa: S310
                log.info(
                    "openai_image_ok model=%s dest=%s via=url refs=%d",
                    model, dest.name, len(refs),
                )
                return dest
            if not b64:
                raise RuntimeError(f"no b64_json in response from {model}")
            _write_b64(dest, b64)
            log.info(
                "openai_image_ok model=%s dest=%s bytes=%d refs=%d",
                model, dest.name, dest.stat().st_size, len(refs),
            )
            return dest
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            log.warning("openai_image_failed model=%s err=%s — trying next", model, exc)

    raise AppError(
        code=ERROR_CODE_INTERNAL,
        message="OpenAI image generation failed",
        http_status_code=502,
        details=[str(last_error), prompt[:200]],
    )
