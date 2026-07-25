"""Visual episode orchestrator — thin wrapper around the crime_v1 pipeline.

Same code path as the offline crime render:
  VisualDirector.plan → ensure_lookbook → render_shots → assemble_episode_video

APIs only split that pipeline:
  POST /visuals/characters  → plan + lookbook
  POST /visuals/render      → (reuse plan) + stills + MP4
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.integrations.images import normalize_image_provider
from app.schemas.visuals import CharacterLook, EpisodeVisualPlan
from app.services.visuals.director import VisualDirector
from app.services.visuals.lookbook import ensure_lookbook
from app.services.visuals.renderer import render_shots
from app.services.visuals.video import assemble_episode_video

log = logging.getLogger(__name__)


class VisualEpisodeService:
    def out_dir(self, series_id: str) -> Path:
        return Path(settings.data_dir) / "visuals" / series_id

    def tts_dir(self, series_id: str) -> Path:
        return Path(settings.data_dir) / "tts" / series_id

    def characters_path(self, series_id: str) -> Path:
        return self.out_dir(series_id) / "characters.json"

    def plan_path(self, series_id: str) -> Path:
        return self.out_dir(series_id) / "plan.json"

    def load_audio_result(self, series_id: str) -> dict[str, Any] | None:
        candidates = [
            self.out_dir(series_id) / "audio_result.json",
            self.tts_dir(series_id) / "audio_result.json",
            self.tts_dir(f"visual_{series_id}") / "audio_result.json",
        ]
        for path in candidates:
            if path.exists():
                data = json.loads(path.read_text())
                log.info("audio_result_loaded %s duration=%.1fs", path, data.get("duration_sec") or 0)
                return data
        return None

    def load_characters(self, series_id: str) -> EpisodeVisualPlan | None:
        path = self.characters_path(series_id)
        if not path.exists():
            return None
        return EpisodeVisualPlan.model_validate_json(path.read_text())

    def load_plan(self, series_id: str) -> EpisodeVisualPlan | None:
        path = self.plan_path(series_id)
        if not path.exists():
            return None
        return EpisodeVisualPlan.model_validate_json(path.read_text())

    def _persist_audio(self, series_id: str, audio_result: dict[str, Any]) -> Path:
        out_dir = self.out_dir(series_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "audio_result.json"
        path.write_text(json.dumps(audio_result, indent=2, ensure_ascii=False))
        return out_dir

    def _save_characters_from_plan(self, plan: EpisodeVisualPlan, series_id: str) -> Path:
        path = self.characters_path(series_id)
        doc = EpisodeVisualPlan(
            series_id=series_id,
            title=plan.title,
            language=plan.language,
            style=plan.style,
            characters=plan.characters,
        )
        path.write_text(doc.model_dump_json(indent=2))
        return path

    def _merge_locked_characters(self, plan: EpisodeVisualPlan, series_id: str) -> None:
        locked = self.load_characters(series_id)
        if not locked or not locked.characters:
            return
        by_id = {c.id.upper(): c for c in locked.characters}
        merged: list[CharacterLook] = []
        seen: set[str] = set()
        for c in plan.characters:
            lock = by_id.get(c.id.upper())
            if lock:
                merged.append(lock.model_copy(deep=True))
                seen.add(lock.id.upper())
            else:
                merged.append(c)
                seen.add(c.id.upper())
        for cid, lock in by_id.items():
            if cid not in seen:
                merged.append(lock.model_copy(deep=True))
        plan.characters = merged
        if locked.style and (locked.style.film_look or locked.style.era_setting):
            plan.style = locked.style
        log.info("merged_locked_characters count=%d", len(plan.characters))

    def build_lookbook(
        self,
        package: dict[str, Any],
        audio_result: dict[str, Any],
        *,
        series_id: str,
        image_provider: str | None = None,
        use_llm_director: bool = True,
        force: bool = False,
    ) -> dict[str, Any]:
        """Same director plan as crime_v1, then lookbook images only (no video)."""
        provider = normalize_image_provider(image_provider)
        out_dir = self._persist_audio(series_id, audio_result)

        timeline = audio_result.get("timeline") or []
        duration = float(audio_result.get("duration_sec") or 0.0)
        if not timeline or duration <= 0:
            raise ValueError("audio result has no timeline — render audiobook first")

        # Exact same director call as render_episode / crime_v1
        plan = VisualDirector().plan(
            package, timeline, duration,
            series_id=series_id, use_llm=use_llm_director,
        )
        ensure_lookbook(plan, out_dir, image_provider=provider, force=force)

        plan_path = self.plan_path(series_id)
        plan_path.write_text(plan.model_dump_json(indent=2))
        chars_path = self._save_characters_from_plan(plan, series_id)

        log.info(
            "lookbook_built series=%s provider=%s characters=%d shots_planned=%d",
            series_id, provider, len(plan.characters), len(plan.shots),
        )
        return {
            "series_id": series_id,
            "image_provider": provider,
            "status": "ready",
            "characters_path": str(chars_path),
            "plan_path": str(plan_path),
            "shot_count": len(plan.shots),
            "characters": [
                {
                    "id": c.id,
                    "name": c.name,
                    "appearance": c.appearance,
                    "wardrobe": c.wardrobe,
                    "facing": c.facing,
                    "reference_image": c.reference_image,
                }
                for c in plan.characters
            ],
            "style": plan.style.model_dump(),
            "lookbook": {c.id: c.reference_image for c in plan.characters},
        }

    def render_episode(
        self,
        package: dict[str, Any],
        audio_result: dict[str, Any],
        *,
        series_id: str,
        use_llm_director: bool = True,
        plan_only: bool = False,
        image_provider: str | None = None,
        require_lookbook: bool = False,
        reuse_plan: bool = True,
    ) -> dict[str, Any]:
        """Same pipeline as crime_v1 offline render.

        If characters step already ran, reuses that plan + lookbook sheets
        (no prompt change) and only generates scene stills + muxes video.
        """
        provider = normalize_image_provider(image_provider)
        out_dir = self._persist_audio(series_id, audio_result)

        timeline = audio_result.get("timeline") or []
        duration = float(audio_result.get("duration_sec") or 0.0)
        if not timeline or duration <= 0:
            raise ValueError("audio result has no timeline — render audiobook first")

        locked = self.load_characters(series_id)
        if require_lookbook and (locked is None or not locked.characters):
            raise ValueError(
                "lookbook not built — call POST /api/v1/visuals/characters first"
            )

        log.info("visual_render series=%s image_provider=%s duration=%.1fs", series_id, provider, duration)

        existing = self.load_plan(series_id) if reuse_plan else None
        if existing and existing.shots and existing.characters:
            plan = existing
            self._merge_locked_characters(plan, series_id)
            log.info("reusing_existing_plan shots=%d", len(plan.shots))
        else:
            plan = VisualDirector().plan(
                package, timeline, duration,
                series_id=series_id, use_llm=use_llm_director,
            )
            self._merge_locked_characters(plan, series_id)

        plan_path = self.plan_path(series_id)
        plan_path.write_text(plan.model_dump_json(indent=2))

        if plan_only:
            return {
                "series_id": series_id,
                "image_provider": provider,
                "plan": json.loads(plan.model_dump_json()),
                "plan_path": str(plan_path),
                "video_path": None,
                "status": "planned",
            }

        # Same lookbook + stills + video assembly as crime_v1
        ensure_lookbook(plan, out_dir, image_provider=provider, force=False)
        self._save_characters_from_plan(plan, series_id)
        plan_path.write_text(plan.model_dump_json(indent=2))

        stills = render_shots(plan, out_dir, image_provider=provider)
        video_path = assemble_episode_video(
            plan, stills, audio_result.get("preview_mp3"), out_dir,
        )

        return {
            "series_id": series_id,
            "image_provider": provider,
            "plan_path": str(plan_path),
            "shot_count": len(plan.shots),
            "stills_rendered": len(stills),
            "lookbook": {c.id: c.reference_image for c in plan.characters},
            "video_path": str(video_path),
            "duration_sec": duration,
            "status": "ready",
        }
