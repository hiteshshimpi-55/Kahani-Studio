from uuid import UUID

from pydantic import BaseModel, Field


class AssetOut(BaseModel):
    id: UUID
    kind: str
    file_path: str
    model: str | None = None
    seed: int | None = None


class CharacterOut(BaseModel):
    id: UUID
    name: str
    role: str
    gender: str | None = None
    age_band: str | None = None
    identity_tokens: str
    voice_provider_id: str | None = None
    locked: bool
    assets: list[AssetOut] = Field(default_factory=list)


class LocationOut(BaseModel):
    id: UUID
    name: str
    description: str
    locked: bool
    assets: list[AssetOut] = Field(default_factory=list)


class SeriesOut(BaseModel):
    id: UUID
    title: str
    language: str
    style_bible: dict
    characters: list[CharacterOut] = Field(default_factory=list)
    locations: list[LocationOut] = Field(default_factory=list)
