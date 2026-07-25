"""Render VisualTrack shots to still images with locked face refs."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.errors.constants import (
    ERROR_CODE_IDENTITY_NOT_FOUND,
    ERROR_MSG_IDENTITY_NOT_FOUND,
)
from app.errors.exceptions import AppError
from app.integrations.replicate.scene import generate_scene_still
from app.repository.models.series import Character, Location, Series
from app.repository.models.visual import VisualShotAsset, VisualTrackRecord
from app.schemas.visual.track import (
    CharacterIdentitySheet,
    LocationSheet,
    StyleBible,
    VisualDirectorInput,
    VisualShot,
    VisualTrack,
)
from app.services.visual.director import VisualDirectorService
from app.services.visual.prompt_compiler import compile_shot_prompt, should_use_face_lock

log = logging.getLogger(__name__)


def _series_dir(series_id: UUID) -> Path:
    return Path(settings.data_dir) / "visual" / str(series_id)


def sheets_from_series(series: Series) -> tuple[list[CharacterIdentitySheet], list[LocationSheet]]:
    identity: list[CharacterIdentitySheet] = []
    for c in series.characters or []:
        turnaround: dict[str, str] = {}
        exprs: dict[str, str] = {}
        for a in c.assets or []:
            if a.kind.startswith("turnaround_"):
                turnaround[a.kind.replace("turnaround_", "")] = a.file_path
            elif a.kind.startswith("expr_"):
                exprs[a.kind.replace("expr_", "")] = a.file_path
        identity.append(
            CharacterIdentitySheet(
                character_id=str(c.id),
                display_name=c.name,
                identity_tokens=c.identity_tokens,
                turnaround_urls=turnaround,
                expression_grid_urls=exprs,
                voice_provider_id=c.voice_provider_id,
            )
        )
    locations: list[LocationSheet] = []
    for loc in series.locations or []:
        locations.append(
            LocationSheet(
                location_id=str(loc.id),
                name=loc.name,
                description=loc.description,
                ref_urls=[a.file_path for a in (loc.assets or [])],
            )
        )
    return identity, locations


class VisualRenderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.director = VisualDirectorService()

    async def plan(
        self,
        *,
        series_id: UUID,
        part: int,
        beats: list[dict],
        narration_sequence: list[dict] | None = None,
        seq_timings: dict[str, dict[str, float]] | None = None,
        part_duration_sec: float,
        persist: bool = True,
    ) -> VisualTrack:
        series = await self._load_series(series_id)
        identity, locations = sheets_from_series(series)
        style_raw = series.style_bible or {}
        style = StyleBible.model_validate(
            {
                **style_raw,
                "series_id": str(series.id),
            }
        )
        # Remap beat speaker / location names → sheet ids when possible
        beats = self._remap_beats(beats, series)
        track = self.director.plan(
            VisualDirectorInput(
                series_id=str(series.id),
                part=part,
                language=series.language,
                style_bible=style,
                identity_sheets=identity,
                location_sheets=locations,
                beats=beats,
                narration_sequence=narration_sequence or [],
                seq_timings=seq_timings or {},
                part_duration_sec=part_duration_sec,
            )
        )
        # Compile prompts onto shots
        for shot in track.shots:
            prompt, neg = compile_shot_prompt(
                shot,
                style=style,
                identity_sheets=identity,
                location_sheets=locations,
            )
            shot.compiled_prompt = prompt
            shot.negative_prompt = neg

        if persist:
            await self._upsert_track(series.id, part, track)
        return track

    async def render_track(
        self,
        *,
        series_id: UUID,
        part: int,
        track: VisualTrack | None = None,
        max_shots: int | None = None,
    ) -> VisualTrack:
        series = await self._load_series(series_id)
        identity, locations = sheets_from_series(series)
        style = StyleBible.model_validate(
            {**(series.style_bible or {}), "series_id": str(series.id)}
        )

        if track is None:
            record = await self._get_track_record(series.id, part)
            if not record:
                raise AppError(
                    code=ERROR_CODE_IDENTITY_NOT_FOUND,
                    message="No visual track planned for this series/part",
                    http_status_code=404,
                )
            track = VisualTrack.model_validate(record.track_json)
        else:
            record = await self._upsert_track(series.id, part, track)

        out_dir = _series_dir(series.id) / "parts" / f"p{part}"
        out_dir.mkdir(parents=True, exist_ok=True)

        shots = track.shots[: max_shots or len(track.shots)]
        for shot in shots:
            if not shot.compiled_prompt:
                prompt, neg = compile_shot_prompt(
                    shot,
                    style=style,
                    identity_sheets=identity,
                    location_sheets=locations,
                )
                shot.compiled_prompt = prompt
                shot.negative_prompt = neg

            dest = out_dir / f"{shot.shot_id}.webp"
            if dest.is_file() and dest.stat().st_size > 0:
                shot.asset_url = str(dest)
                await self._save_shot_asset(record.id, shot.shot_id, str(dest))
                log.info("shot_skipped_existing shot=%s path=%s", shot.shot_id, dest)
                continue

            face_ref = self._face_ref_for_shot(shot, identity)
            if not should_use_face_lock(shot):
                # Wide / two-shot cinematic scenes: Flux with text identity, not PuLID zoom.
                face_ref = None
            result = generate_scene_still(
                compiled_prompt=shot.compiled_prompt,
                face_ref_path=face_ref,
                negative_prompt=shot.negative_prompt,
                dest=dest,
            )
            shot.asset_url = result["file_path"]
            await self._save_shot_asset(record.id, shot.shot_id, result["file_path"])
            log.info("shot_rendered shot=%s path=%s", shot.shot_id, result["file_path"])

        record.track_json = track.model_dump(mode="json")
        await self.session.flush()
        return track

    async def get_timeline(self, series_id: UUID, part: int) -> dict[str, Any]:
        record = await self._get_track_record(series_id, part)
        if not record:
            raise AppError(
                code=ERROR_CODE_IDENTITY_NOT_FOUND,
                message="No visual track for timeline",
                http_status_code=404,
            )
        track = VisualTrack.model_validate(record.track_json)
        return {
            "series_id": str(series_id),
            "part": part,
            "aspect_ratio": track.aspect_ratio,
            "density": track.density,
            "items": [
                {
                    "shot_id": s.shot_id,
                    "t_start_sec": s.t_start_sec,
                    "t_end_sec": s.t_end_sec,
                    "media_kind": s.media_kind,
                    "asset_url": s.asset_url,
                    "visual_intent": s.visual_intent,
                    "trigger_reason": s.trigger_reason,
                    "view": s.view.model_dump() if s.view else None,
                }
                for s in track.shots
            ],
        }

    def _face_ref_for_shot(
        self, shot: VisualShot, identity: list[CharacterIdentitySheet]
    ) -> str | None:
        if not shot.characters:
            return None
        primary = shot.characters[0]
        if primary.face_ref_url:
            return primary.face_ref_url
        for sheet in identity:
            if sheet.character_id == primary.character_id:
                return (sheet.turnaround_urls or {}).get("front") or next(
                    iter((sheet.turnaround_urls or {}).values()), None
                )
        return None

    def _remap_beats(self, beats: list[dict], series: Series) -> list[dict]:
        name_to_char = {c.name.upper(): c for c in (series.characters or [])}
        name_to_loc = {loc.name.upper(): loc for loc in (series.locations or [])}
        out: list[dict] = []
        for b in beats:
            beat = dict(b)
            sp = beat.get("speaker")
            if isinstance(sp, str) and sp.upper() in name_to_char:
                beat["speaker"] = str(name_to_char[sp.upper()].id)
                beat["role"] = name_to_char[sp.upper()].role
            loc = beat.get("location_id") or beat.get("location") or beat.get("setting")
            if isinstance(loc, str):
                key = loc.upper()
                # fuzzy: exact name or contained
                match = name_to_loc.get(key)
                if not match:
                    for n, L in name_to_loc.items():
                        if n in key or key in n:
                            match = L
                            break
                if match:
                    beat["location_id"] = str(match.id)
            out.append(beat)
        return out

    async def _load_series(self, series_id: UUID) -> Series:
        result = await self.session.execute(
            select(Series)
            .where(Series.id == series_id)
            .options(
                selectinload(Series.characters).selectinload(Character.assets),
                selectinload(Series.locations).selectinload(Location.assets),
            )
        )
        series = result.scalar_one_or_none()
        if not series:
            raise AppError(
                code=ERROR_CODE_IDENTITY_NOT_FOUND,
                message=ERROR_MSG_IDENTITY_NOT_FOUND,
                http_status_code=404,
            )
        return series

    async def _get_track_record(
        self, series_id: UUID, part: int
    ) -> VisualTrackRecord | None:
        result = await self.session.execute(
            select(VisualTrackRecord).where(
                VisualTrackRecord.series_id == series_id,
                VisualTrackRecord.part == part,
            )
        )
        return result.scalar_one_or_none()

    async def _upsert_track(
        self, series_id: UUID, part: int, track: VisualTrack
    ) -> VisualTrackRecord:
        record = await self._get_track_record(series_id, part)
        payload = track.model_dump(mode="json")
        if record:
            record.track_json = payload
        else:
            record = VisualTrackRecord(
                id=uuid.uuid4(),
                series_id=series_id,
                part=part,
                track_json=payload,
            )
            self.session.add(record)
        await self.session.flush()
        return record

    async def _save_shot_asset(
        self, track_id: UUID, shot_id: str, file_path: str
    ) -> None:
        result = await self.session.execute(
            select(VisualShotAsset).where(
                VisualShotAsset.track_id == track_id,
                VisualShotAsset.shot_id == shot_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.file_path = file_path
        else:
            self.session.add(
                VisualShotAsset(
                    id=uuid.uuid4(),
                    track_id=track_id,
                    shot_id=shot_id,
                    file_path=file_path,
                )
            )
        await self.session.flush()
