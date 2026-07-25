"""Identity sheet image generation via Flux + PuLID."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.integrations.replicate.client import (
    download_to_path,
    local_or_http_face_ref,
    run_model,
)

log = logging.getLogger(__name__)

DEFAULT_NEGATIVE = (
    "bad quality, worst quality, text, signature, watermark, extra limbs, "
    "deformed eyes, blurry, low resolution, cartoon watermark"
)


def generate_face_sheet(
    *,
    identity_tokens: str,
    style: str = "cinematic film still, photorealistic",
    seed: int | None = None,
    width: int | None = None,
    height: int | None = None,
    dest: Path,
) -> dict[str, Any]:
    """Text-to-image front portrait for a character identity sheet."""
    seed = seed if seed is not None else random.randint(1, 2_147_483_647)
    width = width or settings.replicate_default_width
    height = height or settings.replicate_default_height
    prompt = (
        f"Portrait photo of a person. {identity_tokens}. "
        f"Front-facing head and shoulders, neutral expression, clean background. "
        f"Style: {style}. No text, no watermark."
    )
    model = settings.replicate_face_model
    url = run_model(
        model,
        {
            "prompt": prompt,
            "num_outputs": 1,
            "aspect_ratio": "9:16" if height > width else "1:1",
            "output_format": "webp",
            "output_quality": 90,
            "seed": seed,
        },
    )
    path = download_to_path(url, dest)
    return {
        "file_path": str(path),
        "seed": seed,
        "model": model,
        "prompt": prompt,
        "url": url,
    }


def generate_expression(
    *,
    face_ref_path: str,
    expression: str,
    style: str = "cinematic film still, photorealistic",
    identity_tokens: str = "",
    seed: int | None = None,
    dest: Path,
) -> dict[str, Any]:
    """Expression variant locked to the identity face via Flux-PuLID."""
    seed = seed if seed is not None else random.randint(1, 2_147_483_647)
    prompt = (
        f"Portrait of the same person, expression: {expression}. "
        f"{identity_tokens}. Close-up face, {style}. No text."
    )
    model = settings.replicate_pulid_model
    face = local_or_http_face_ref(face_ref_path)
    try:
        url = run_model(
            model,
            {
                "main_face_image": face,
                "prompt": prompt,
                "negative_prompt": DEFAULT_NEGATIVE,
                "width": settings.replicate_default_width,
                "height": settings.replicate_default_height,
                "num_steps": 20,
                "start_step": 4,
                "id_weight": 1.0,
                "guidance_scale": 4,
                "seed": seed,
                "output_format": "webp",
                "output_quality": 90,
                "num_outputs": 1,
            },
        )
    finally:
        if hasattr(face, "close"):
            face.close()
    path = download_to_path(url, dest)
    return {
        "file_path": str(path),
        "seed": seed,
        "model": model,
        "prompt": prompt,
        "url": url,
    }


def generate_location_ref(
    *,
    description: str,
    kind: str = "night",
    style: str = "cinematic film still",
    seed: int | None = None,
    dest: Path,
) -> dict[str, Any]:
    """Background / location reference still (no face)."""
    seed = seed if seed is not None else random.randint(1, 2_147_483_647)
    prompt = (
        f"Empty establishing location plate, {kind}. {description}. "
        f"No people, no faces. Style: {style}. Photorealistic, 9:16."
    )
    model = settings.replicate_face_model
    url = run_model(
        model,
        {
            "prompt": prompt,
            "num_outputs": 1,
            "aspect_ratio": "9:16",
            "output_format": "webp",
            "output_quality": 90,
            "seed": seed,
        },
    )
    path = download_to_path(url, dest)
    return {
        "file_path": str(path),
        "seed": seed,
        "model": model,
        "prompt": prompt,
        "url": url,
    }
