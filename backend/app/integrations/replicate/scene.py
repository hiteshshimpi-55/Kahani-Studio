"""Scene still generation with face-locked PuLID."""

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
from app.integrations.replicate.identity import DEFAULT_NEGATIVE

log = logging.getLogger(__name__)


def generate_scene_still(
    *,
    compiled_prompt: str,
    face_ref_path: str | None,
    negative_prompt: str | None = None,
    seed: int | None = None,
    width: int | None = None,
    height: int | None = None,
    dest: Path,
) -> dict[str, Any]:
    """Generate a companion still. Uses PuLID when a face ref is provided."""
    seed = seed if seed is not None else random.randint(1, 2_147_483_647)
    width = width or settings.replicate_default_width
    height = height or settings.replicate_default_height
    neg = negative_prompt or DEFAULT_NEGATIVE

    if face_ref_path:
        model = settings.replicate_pulid_model
        face = local_or_http_face_ref(face_ref_path)
        try:
            url = run_model(
                model,
                {
                    "main_face_image": face,
                    "prompt": compiled_prompt,
                    "negative_prompt": neg,
                    "width": width,
                    "height": height,
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
    else:
        # Establishing / insert with no on-screen character face
        model = settings.replicate_face_model
        url = run_model(
            model,
            {
                "prompt": compiled_prompt,
                "num_outputs": 1,
                "aspect_ratio": "9:16" if height >= width else "16:9",
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
        "prompt": compiled_prompt,
        "url": url,
    }
