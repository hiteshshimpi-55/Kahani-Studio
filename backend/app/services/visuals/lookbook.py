"""Character lookbook — one locked reference image per character.

The reference sheet is generated once and then passed into every scene
render so faces and wardrobe stay identical across shots (Nano Banana
character-consistency technique).
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.integrations.images import generate_image
from app.schemas.visuals import EpisodeVisualPlan
from app.services.visuals.prompts import build_lookbook_prompt

log = logging.getLogger(__name__)


def ensure_lookbook(
    plan: EpisodeVisualPlan,
    out_dir: Path,
    *,
    image_provider: str | None = None,
    force: bool = False,
) -> None:
    """Generate (or reuse) a reference sheet for every character."""
    lookbook_dir = out_dir / "lookbook"
    lookbook_dir.mkdir(parents=True, exist_ok=True)

    for char in plan.characters:
        dest = lookbook_dir / f"{char.id.lower()}.png"
        if dest.exists() and dest.stat().st_size > 0 and not force:
            char.reference_image = str(dest)
            log.info("lookbook_reuse %s", char.id)
            continue
        story_day = next(iter(char.wardrobe.keys()), "day1")
        prompt = build_lookbook_prompt(char, plan, story_day)
        generate_image(
            prompt, dest=dest, aspect_ratio="3:4", image_provider=image_provider,
        )
        char.reference_image = str(dest)
        log.info("lookbook_ok %s -> %s", char.id, dest.name)
