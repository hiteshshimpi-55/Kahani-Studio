"""Visual episode orchestrator — director → lookbook → stills → MP4.

Working files stay under DATA_DIR only as ephemeral cache.
Canonical blobs live in S3; Postgres ``visual_media_assets`` maps them.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.integrations.images import normalize_image_provider
from app.schemas.visuals import CharacterLook, EpisodeVisualPlan
from app.services.visuals import artifacts
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

    def _publish_json(self, path: Path, series_id: str, kind: str) -> None:
        artifacts.publish(path, series_id=series_id, kind=kind, delete_local=False)

    def _hydrate_json(self, path: Path, series_id: str, kind: str) -> Path | None:
        return artifacts.ensure_local(path, series_id=series_id, kind=kind)

    def load_audio_result(self, series_id: str) -> dict[str, Any] | None:
        candidates = [
            (self.out_dir(series_id) / "audio_result.json", artifacts.KIND_AUDIO, series_id),
            (self.tts_dir(series_id) / "audio_result.json", artifacts.KIND_TTS, series_id),
            (
                self.tts_dir(f"visual_{series_id}") / "audio_result.json",
                artifacts.KIND_TTS,
                f"visual_{series_id}",
            ),
        ]
        for path, kind, sid in candidates:
            got = artifacts.ensure_local(path, series_id=sid, kind=kind)
            if got is not None and got.exists():
                data = json.loads(got.read_text())
                # Prefer TTS series id for mp3 hydration when loading from tts/
                tts_sid = sid if kind == artifacts.KIND_TTS else series_id
                # Also try visual_{series} and plain series under tts
                for try_sid in (tts_sid, series_id, f"visual_{series_id}"):
                    artifacts.hydrate_audio_paths(try_sid, data)
                    if data.get("preview_mp3") and Path(str(data["preview_mp3"])).exists():
                        break
                log.info(
                    "audio_result_loaded %s duration=%.1fs",
                    got, data.get("duration_sec") or 0,
                )
                return data
        return None

    def load_characters(self, series_id: str) -> EpisodeVisualPlan | None:
        path = self.characters_path(series_id)
        got = artifacts.ensure_local(path, series_id=series_id, kind=artifacts.KIND_CHARACTERS)
        if got is None:
            return None
        return EpisodeVisualPlan.model_validate_json(got.read_text())

    def load_plan(self, series_id: str) -> EpisodeVisualPlan | None:
        path = self.plan_path(series_id)
        got = artifacts.ensure_local(path, series_id=series_id, kind=artifacts.KIND_PLAN)
        if got is None:
            return None
        return EpisodeVisualPlan.model_validate_json(got.read_text())

    def _persist_audio(self, series_id: str, audio_result: dict[str, Any]) -> Path:
        out_dir = self.out_dir(series_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "audio_result.json"
        path.write_text(json.dumps(audio_result, indent=2, ensure_ascii=False))
        self._publish_json(path, series_id, artifacts.KIND_AUDIO)
        return out_dir

    def _save_characters_from_plan(self, plan: EpisodeVisualPlan, series_id: str) -> Path:
        path = self.characters_path(series_id)
        # Persist S3 URLs in reference_image when available (API-friendly).
        lookbook_urls = artifacts.urls_by_kind(series_id, artifacts.KIND_LOOKBOOK)
        chars = []
        for c in plan.characters:
            copy = c.model_copy(deep=True)
            url = lookbook_urls.get(f"{c.id.lower()}.png")
            if url:
                copy.reference_image = url
            chars.append(copy)
        doc = EpisodeVisualPlan(
            series_id=series_id,
            title=plan.title,
            language=plan.language,
            style=plan.style,
            characters=chars,
        )
        path.write_text(doc.model_dump_json(indent=2))
        self._publish_json(path, series_id, artifacts.KIND_CHARACTERS)
        return path

    def _save_plan(self, plan: EpisodeVisualPlan, series_id: str) -> Path:
        path = self.plan_path(series_id)
        path.write_text(plan.model_dump_json(indent=2))
        self._publish_json(path, series_id, artifacts.KIND_PLAN)
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

    def _lookbook_response(self, series_id: str, plan: EpisodeVisualPlan) -> dict[str, str]:
        urls = artifacts.urls_by_kind(series_id, artifacts.KIND_LOOKBOOK)
        out: dict[str, str] = {}
        for c in plan.characters:
            key = f"{c.id.lower()}.png"
            out[c.id] = urls.get(key) or c.reference_image or ""
        return out

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
        """Director plan + lookbook images; publish sheets to S3."""
        provider = normalize_image_provider(image_provider)
        out_dir = self._persist_audio(series_id, audio_result)

        timeline = audio_result.get("timeline") or []
        duration = float(audio_result.get("duration_sec") or 0.0)
        if not timeline or duration <= 0:
            raise ValueError("audio result has no timeline — render audiobook first")

        plan = VisualDirector().plan(
            package, timeline, duration,
            series_id=series_id, use_llm=use_llm_director,
        )
        ensure_lookbook(
            plan, out_dir, series_id=series_id, image_provider=provider, force=force,
        )

        plan_path = self._save_plan(plan, series_id)
        chars_path = self._save_characters_from_plan(plan, series_id)
        lookbook = self._lookbook_response(series_id, plan)

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
                    "reference_image": lookbook.get(c.id) or c.reference_image,
                }
                for c in plan.characters
            ],
            "style": plan.style.model_dump(),
            "lookbook": lookbook,
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
        force_lookbook: bool = False,
        force_stills: bool = False,
    ) -> dict[str, Any]:
        """Stills + MP4; publish to S3 and return URLs.

        Director always RAG-retrieves shot_template rows from Databricks
        Vector Search (local catalog fallback) before planning.
        """
        provider = normalize_image_provider(image_provider)
        out_dir = self._persist_audio(series_id, audio_result)

        timeline = audio_result.get("timeline") or []
        duration = float(audio_result.get("duration_sec") or 0.0)
        if not timeline or duration <= 0:
            raise ValueError("audio result has no timeline — render audiobook first")

        locked = self.load_characters(series_id)
        if require_lookbook and not force_lookbook and (locked is None or not locked.characters):
            raise ValueError(
                "lookbook not built — call POST /api/v1/visuals/characters first"
            )

        log.info(
            "visual_render series=%s image_provider=%s duration=%.1fs force_stills=%s",
            series_id, provider, duration, force_stills,
        )

        existing = self.load_plan(series_id) if reuse_plan and not force_stills else None
        if existing and existing.shots and existing.characters and not force_lookbook:
            plan = existing
            self._merge_locked_characters(plan, series_id)
            log.info("reusing_existing_plan shots=%d", len(plan.shots))
        else:
            # Fresh plan → vector search for shot_template + Gemini director
            plan = VisualDirector().plan(
                package, timeline, duration,
                series_id=series_id, use_llm=use_llm_director,
            )
            if not force_lookbook:
                self._merge_locked_characters(plan, series_id)

        plan_path = self._save_plan(plan, series_id)

        if plan_only:
            return {
                "series_id": series_id,
                "image_provider": provider,
                "plan": json.loads(plan.model_dump_json()),
                "plan_path": str(plan_path),
                "video_url": None,
                "status": "planned",
            }

        ensure_lookbook(
            plan,
            out_dir,
            series_id=series_id,
            image_provider=provider,
            force=force_lookbook,
        )
        self._save_characters_from_plan(plan, series_id)
        self._save_plan(plan, series_id)

        stills = render_shots(
            plan,
            out_dir,
            series_id=series_id,
            image_provider=provider,
            force=bool(force_stills),
        )
        video_path = assemble_episode_video(
            plan, stills, audio_result.get("preview_mp3"), out_dir,
        )
        artifacts.publish(
            video_path,
            series_id=series_id,
            kind=artifacts.KIND_VIDEO,
            asset_key="episode.mp4",
            delete_local=True,  # S3 is canonical; drop local MP4 after upload
        )
        lookbook = self._lookbook_response(series_id, plan)
        shot_urls = artifacts.urls_by_kind(series_id, artifacts.KIND_SHOT)
        video_url = artifacts.url_for(series_id, artifacts.KIND_VIDEO, "episode.mp4")

        return {
            "series_id": series_id,
            "image_provider": provider,
            "plan_path": str(plan_path),
            "shot_count": len(plan.shots),
            "stills_rendered": len(stills),
            "lookbook": lookbook,
            "stills": shot_urls,
            "video_url": video_url,
            "video_path": video_url,  # alias for older clients
            "duration_sec": duration,
            "status": "ready",
        }

    def episode_status(self, series_id: str) -> dict[str, Any]:
        """API snapshot from S3 registry (+ hydrated plan JSON)."""
        assets = artifacts.asset_map(series_id)
        lookbook = assets.get(artifacts.KIND_LOOKBOOK, {})
        stills = assets.get(artifacts.KIND_SHOT, {})
        video = assets.get(artifacts.KIND_VIDEO, {}).get("episode.mp4")
        plan = self.load_plan(series_id)
        chars = self.load_characters(series_id)
        audio = self.load_audio_result(series_id)

        if not assets and plan is None and chars is None and audio is None:
            return {"series_id": series_id, "status": "missing"}

        if video:
            status = "ready"
        elif lookbook and chars:
            status = "characters_ready" if not stills else "planned"
        elif audio:
            status = "pending"
        else:
            status = "planned" if plan else "pending"

        return {
            "series_id": series_id,
            "status": status,
            "plan": json.loads(plan.model_dump_json()) if plan else None,
            "lookbook": lookbook,
            "stills": stills,
            "video_url": video,
            "video_path": video,
            "shot_count": len(stills),
            "characters_ready": bool(chars and chars.characters),
            "duration_sec": (audio or {}).get("duration_sec"),
            "assets": assets,
        }

    def characters_status(self, series_id: str) -> dict[str, Any] | None:
        plan = self.load_characters(series_id)
        lookbook = artifacts.urls_by_kind(series_id, artifacts.KIND_LOOKBOOK)
        audio = self.load_audio_result(series_id)
        if plan is None and not lookbook and audio is None:
            return None
        characters = []
        if plan:
            characters = [
                {
                    "id": c.id,
                    "name": c.name,
                    "appearance": c.appearance,
                    "wardrobe": c.wardrobe,
                    "facing": c.facing,
                    "reference_image": lookbook.get(f"{c.id.lower()}.png") or c.reference_image,
                }
                for c in plan.characters
            ]
        ready = bool(characters and lookbook and len(lookbook) >= max(1, len(characters)))
        if ready:
            status = "ready"
        elif lookbook or characters:
            status = "partial"
        else:
            status = "pending"
        return {
            "series_id": series_id,
            "status": status,
            "characters": characters,
            "style": plan.style.model_dump() if plan else None,
            "lookbook_files": sorted(lookbook.keys()),
            "lookbook": (
                {c["id"]: c.get("reference_image") for c in characters}
                if characters
                else {k.replace(".png", "").upper(): v for k, v in lookbook.items()}
            ),
        }
