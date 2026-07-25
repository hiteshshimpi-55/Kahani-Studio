from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.schemas.identity.request import (
    CreateSeriesRequest,
    GenerateCharactersRequest,
    GenerateLocationsRequest,
)
from app.schemas.identity.response import CharacterOut, LocationOut, SeriesOut
from app.services.identity.service import IdentityService

router = APIRouter(prefix="/identity", tags=["identity"])


@router.post("/series", response_model=SeriesOut)
async def create_series(
    body: CreateSeriesRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SeriesOut:
    return await IdentityService(db).create_series(body)


@router.get("/series/{series_id}", response_model=SeriesOut)
async def get_series(
    series_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SeriesOut:
    return await IdentityService(db).get_series(series_id)


@router.post("/characters/generate", response_model=list[CharacterOut])
async def generate_characters(
    body: GenerateCharactersRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CharacterOut]:
    return await IdentityService(db).generate_characters(
        UUID(body.series_id),
        body.characters,
        generate_images=body.generate_images,
    )


@router.post("/characters/{character_id}/lock", response_model=CharacterOut)
async def lock_character(
    character_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterOut:
    return await IdentityService(db).lock_character(character_id)


@router.post("/locations/generate", response_model=list[LocationOut])
async def generate_locations(
    body: GenerateLocationsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LocationOut]:
    return await IdentityService(db).generate_locations(
        UUID(body.series_id),
        body.locations,
        generate_images=body.generate_images,
    )
