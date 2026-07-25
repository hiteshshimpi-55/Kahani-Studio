"""Identity sheet service — faces and locations BEFORE scene stills."""

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
    ERROR_CODE_IDENTITY_LOCKED,
    ERROR_CODE_IDENTITY_NOT_FOUND,
    ERROR_MSG_IDENTITY_LOCKED,
    ERROR_MSG_IDENTITY_NOT_FOUND,
)
from app.errors.exceptions import AppError
from app.integrations.replicate.identity import (
    generate_expression,
    generate_face_sheet,
    generate_location_ref,
)
from app.repository.models.series import Character, CharacterAsset, Location, LocationAsset, Series
from app.schemas.identity.request import (
    CharacterSpec,
    CreateSeriesRequest,
    LocationSpec,
)
from app.schemas.identity.response import AssetOut, CharacterOut, LocationOut, SeriesOut
from app.schemas.visual.track import StyleBible

log = logging.getLogger(__name__)

_EXPR_KIND = {
    "neutral": "expr_neutral",
    "fear": "expr_fear",
    "anger": "expr_anger",
    "whisper": "expr_whisper",
    "gasp": "expr_gasp",
    "dismissive": "expr_dismissive",
    "menace": "expr_menace",
}


def _series_dir(series_id: UUID) -> Path:
    return Path(settings.data_dir) / "visual" / str(series_id)


def _asset_out(a: CharacterAsset | LocationAsset) -> AssetOut:
    return AssetOut(
        id=a.id,
        kind=a.kind,
        file_path=a.file_path,
        model=a.model,
        seed=a.seed,
    )


def _loaded_assets(obj: Character | Location) -> list:
    """Return relationship list without triggering async lazy-load."""
    if "assets" not in obj.__dict__ or obj.__dict__["assets"] is None:
        obj.__dict__["assets"] = []
    return obj.__dict__["assets"]


def _character_out(c: Character) -> CharacterOut:
    return CharacterOut(
        id=c.id,
        name=c.name,
        role=c.role,
        gender=c.gender,
        age_band=c.age_band,
        identity_tokens=c.identity_tokens,
        voice_provider_id=c.voice_provider_id,
        locked=c.locked,
        assets=[_asset_out(a) for a in _loaded_assets(c)],
    )


def _location_out(loc: Location) -> LocationOut:
    return LocationOut(
        id=loc.id,
        name=loc.name,
        description=loc.description,
        locked=loc.locked,
        assets=[_asset_out(a) for a in _loaded_assets(loc)],
    )


def _series_out(s: Series) -> SeriesOut:
    # Avoid sync lazy-load under async (MissingGreenlet) when rels aren't loaded.
    characters = s.__dict__.get("characters") or []
    locations = s.__dict__.get("locations") or []
    return SeriesOut(
        id=s.id,
        title=s.title,
        language=s.language,
        style_bible=s.style_bible or {},
        characters=[_character_out(c) for c in characters],
        locations=[_location_out(loc) for loc in locations],
    )


class IdentityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_series(self, body: CreateSeriesRequest) -> SeriesOut:
        if body.style_bible is not None:
            style = body.style_bible.model_dump(mode="json")
            # Ensure series_id placeholder replaced after insert
        else:
            style = StyleBible(
                series_id="pending",
                look=body.look,
                aspect_ratio=body.aspect_ratio,
                density=body.density,
                max_stills_per_part=body.max_stills_per_part,
                allow_clips=False,
            ).model_dump(mode="json")

        series = Series(
            id=uuid.uuid4(),
            title=body.title,
            language=body.language,
            style_bible=style,
        )
        style["series_id"] = str(series.id)
        series.style_bible = style
        self.session.add(series)
        await self.session.flush()
        _series_dir(series.id).mkdir(parents=True, exist_ok=True)
        return _series_out(series)

    async def get_series(self, series_id: UUID) -> SeriesOut:
        series = await self._load_series(series_id)
        return _series_out(series)

    async def generate_characters(
        self,
        series_id: UUID,
        specs: list[CharacterSpec],
        *,
        generate_images: bool = True,
    ) -> list[CharacterOut]:
        series = await self._load_series(series_id)
        look = (series.style_bible or {}).get("look", "cinematic film still")
        out: list[CharacterOut] = []

        for spec in specs:
            existing = next(
                (c for c in (series.characters or []) if c.name == spec.name), None
            )
            if existing and existing.locked:
                raise AppError(
                    code=ERROR_CODE_IDENTITY_LOCKED,
                    message=ERROR_MSG_IDENTITY_LOCKED,
                    http_status_code=409,
                    details=[spec.name],
                )
            character = existing or Character(
                id=uuid.uuid4(),
                series_id=series.id,
                name=spec.name,
                role=spec.role,
                gender=spec.gender,
                age_band=spec.age_band,
                identity_tokens=spec.identity_tokens,
                voice_provider_id=spec.voice_provider_id,
                locked=False,
            )
            if existing:
                character.identity_tokens = spec.identity_tokens
                character.role = spec.role
                character.gender = spec.gender
                character.age_band = spec.age_band
                character.voice_provider_id = spec.voice_provider_id
            else:
                character.assets = []
                self.session.add(character)
                await self.session.flush()

            if generate_images:
                await self._ensure_front_portrait(character, look=look)
                await self._generate_expressions(character, spec.expressions, look=look)

            await self.session.refresh(character, attribute_names=["assets"])
            out.append(_character_out(character))

        return out

    async def lock_character(self, character_id: UUID) -> CharacterOut:
        result = await self.session.execute(
            select(Character)
            .where(Character.id == character_id)
            .options(selectinload(Character.assets))
        )
        character = result.scalar_one_or_none()
        if not character:
            raise AppError(
                code=ERROR_CODE_IDENTITY_NOT_FOUND,
                message=ERROR_MSG_IDENTITY_NOT_FOUND,
                http_status_code=404,
            )
        front = next(
            (a for a in (character.assets or []) if a.kind == "turnaround_front"), None
        )
        if not front:
            raise AppError(
                code=ERROR_CODE_IDENTITY_NOT_FOUND,
                message="Cannot lock character without turnaround_front asset",
                http_status_code=400,
            )
        character.locked = True
        await self.session.flush()
        return _character_out(character)

    async def generate_locations(
        self,
        series_id: UUID,
        specs: list[LocationSpec],
        *,
        generate_images: bool = True,
    ) -> list[LocationOut]:
        series = await self._load_series(series_id)
        look = (series.style_bible or {}).get("look", "cinematic film still")
        out: list[LocationOut] = []

        for spec in specs:
            existing = next(
                (loc for loc in (series.locations or []) if loc.name == spec.name), None
            )
            location = existing or Location(
                id=uuid.uuid4(),
                series_id=series.id,
                name=spec.name,
                description=spec.description,
                locked=False,
            )
            if existing:
                location.description = spec.description
            else:
                location.assets = []
                self.session.add(location)
                await self.session.flush()

            if generate_images:
                for kind in spec.kinds:
                    await self._ensure_location_asset(location, kind=kind, look=look)

            location.locked = True
            await self.session.refresh(location, attribute_names=["assets"])
            out.append(_location_out(location))

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

    async def _ensure_front_portrait(self, character: Character, *, look: str) -> CharacterAsset:
        assets = _loaded_assets(character)
        existing = next((a for a in assets if a.kind == "turnaround_front"), None)
        if existing:
            return existing
        dest = (
            _series_dir(character.series_id)
            / "identity"
            / f"{character.name}_front.webp"
        )
        result = generate_face_sheet(
            identity_tokens=character.identity_tokens,
            style=look,
            dest=dest,
        )
        asset = CharacterAsset(
            id=uuid.uuid4(),
            character_id=character.id,
            kind="turnaround_front",
            file_path=result["file_path"],
            seed=result.get("seed"),
            model=result.get("model"),
            prompt=result.get("prompt"),
        )
        self.session.add(asset)
        await self.session.flush()
        assets.append(asset)
        return asset

    async def _generate_expressions(
        self, character: Character, expressions: list[str], *, look: str
    ) -> None:
        assets = _loaded_assets(character)
        front = next((a for a in assets if a.kind == "turnaround_front"), None)
        if not front:
            return
        existing_kinds = {a.kind for a in assets}
        for expr in expressions:
            kind = _EXPR_KIND.get(expr.lower(), f"expr_{expr.lower()}")
            if kind in existing_kinds:
                continue
            dest = (
                _series_dir(character.series_id)
                / "identity"
                / f"{character.name}_{kind}.webp"
            )
            result = generate_expression(
                face_ref_path=front.file_path,
                expression=expr,
                style=look,
                identity_tokens=character.identity_tokens,
                dest=dest,
            )
            asset = CharacterAsset(
                id=uuid.uuid4(),
                character_id=character.id,
                kind=kind,
                file_path=result["file_path"],
                seed=result.get("seed"),
                model=result.get("model"),
                prompt=result.get("prompt"),
            )
            self.session.add(asset)
            await self.session.flush()
            assets.append(asset)

    async def _ensure_location_asset(
        self, location: Location, *, kind: str, look: str
    ) -> LocationAsset:
        assets = _loaded_assets(location)
        existing = next((a for a in assets if a.kind == kind), None)
        if existing:
            return existing
        dest = (
            _series_dir(location.series_id)
            / "locations"
            / f"{location.name}_{kind}.webp"
        )
        result = generate_location_ref(
            description=location.description,
            kind=kind,
            style=look,
            dest=dest,
        )
        asset = LocationAsset(
            id=uuid.uuid4(),
            location_id=location.id,
            kind=kind,
            file_path=result["file_path"],
            seed=result.get("seed"),
            model=result.get("model"),
            prompt=result.get("prompt"),
        )
        self.session.add(asset)
        await self.session.flush()
        assets.append(asset)
        return asset

    async def face_ref_for_character(self, character_id: UUID) -> str | None:
        result = await self.session.execute(
            select(CharacterAsset)
            .where(
                CharacterAsset.character_id == character_id,
                CharacterAsset.kind == "turnaround_front",
            )
            .limit(1)
        )
        asset = result.scalar_one_or_none()
        return asset.file_path if asset else None
