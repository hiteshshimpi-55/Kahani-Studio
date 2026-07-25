"""Scene still renderer — one 9:16 frame per shot, conditioned on the
character lookbook references so identity persists across the episode."""

from __future__ import annotations

import logging
from pathlib import Path

from app.integrations.images import generate_image
from app.schemas.visuals import EpisodeVisualPlan
from app.services.visuals import artifacts
from app.services.visuals.prompts import build_shot_prompt

log = logging.getLogger(__name__)

MAX_REFS_PER_SHOT = 4  # group / lab shots need doctor + multiple officers


def render_shots(
    plan: EpisodeVisualPlan,
    out_dir: Path,
    *,
    series_id: str,
    image_provider: str | None = None,
    force: bool = False,
) -> dict[str, str]:
    """Render every shot still. Returns shot_id → local working path."""
    shots_dir = out_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    # Materialize lookbook refs for image conditioning
    for char in plan.characters:
        dest = out_dir / "lookbook" / f"{char.id.lower()}.png"
        local = artifacts.ensure_local(
            dest, series_id=series_id, kind=artifacts.KIND_LOOKBOOK,
        )
        if local is not None:
            char.reference_image = str(local)

    results: dict[str, str] = {}
    for shot in plan.shots:
        dest = shots_dir / f"{shot.shot_id}.png"
        if not force:
            cached = artifacts.ensure_local(
                dest, series_id=series_id, kind=artifacts.KIND_SHOT,
            )
            if cached is not None:
                results[shot.shot_id] = str(cached)
                log.info("shot_reuse %s", shot.shot_id)
                continue
        elif dest.exists():
            dest.unlink(missing_ok=True)

        scene = plan.scene(shot.scene_id) or (plan.scenes[0] if plan.scenes else None)
        if scene is None:
            log.warning("shot %s has no scene — skipping", shot.shot_id)
            continue

        ref_chars = []
        for cid in shot.characters_on_screen[:MAX_REFS_PER_SHOT]:
            char = plan.character(cid)
            if char and char.reference_image:
                ref_chars.append(char)

        prompt = build_shot_prompt(shot, scene, plan, ref_chars)
        try:
            generate_image(
                prompt,
                reference_image_paths=[c.reference_image for c in ref_chars if c.reference_image],
                dest=dest,
                aspect_ratio="9:16",
                image_provider=image_provider,
            )
            artifacts.publish(
                dest,
                series_id=series_id,
                kind=artifacts.KIND_SHOT,
                delete_local=False,  # keep for ffmpeg in this job
            )
            results[shot.shot_id] = str(dest)
            log.info(
                "shot_ok %s size=%s refs=%d [%.1f-%.1f]",
                shot.shot_id, shot.shot_size, len(ref_chars), shot.t_start, shot.t_end,
            )
        except Exception:
            log.exception("shot_failed %s — will reuse previous frame in video", shot.shot_id)
    return results
