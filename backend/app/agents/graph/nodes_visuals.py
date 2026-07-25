"""Cover art generation helpers (used by ARQ cover job)."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from app.integrations.images import generate_image
from app.integrations.s3 import get_artifact_storage
from app.services.projects.stages import build_cover_prompt, run_cover_key

logger = logging.getLogger(__name__)


def generate_and_store_cover(
    *,
    project_id: str,
    run_id: str,
    package: dict[str, Any],
    audio_result: dict[str, Any] | None = None,
    revision_notes: str | None = None,
    image_provider: str | None = None,
) -> str:
    """Generate cover PNG and push to S3. Returns object key."""
    prompt = build_cover_prompt(
        package,
        audio_result=audio_result,
        revision_notes=revision_notes,
    )
    cover_key = run_cover_key(project_id, run_id)

    with tempfile.TemporaryDirectory(prefix="kissa-cover-") as tmp:
        dest = Path(tmp) / "cover.png"
        generate_image(
            prompt,
            dest=dest,
            aspect_ratio="9:16",
            image_provider=image_provider,
        )
        if not dest.is_file() or dest.stat().st_size == 0:
            raise RuntimeError("cover image generation produced empty file")
        get_artifact_storage().put_bytes(
            cover_key,
            dest.read_bytes(),
            content_type="image/png",
        )

    logger.info(
        "cover_art_stored project=%s run=%s key=%s",
        project_id,
        run_id,
        cover_key,
    )
    return cover_key
