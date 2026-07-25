from pydantic import BaseModel, Field


class CastCandidate(BaseModel):
    rank: int
    id: str | None = None
    provider: str | None = None
    provider_id: str | None = None
    name: str | None = None
    asset_type: str | None = None
    language: str | None = None
    gender: str | None = None
    preview_url: str | None = None
    free_users_allowed: bool | None = None
    description: str | None = None
    sfx_prompt: str | None = None
    score: float | None = None
    raw: dict = Field(default_factory=dict)


class CharacterCastResult(BaseModel):
    character_id: str
    role: str
    query: str
    primary: CastCandidate | None = None
    alternatives: list[CastCandidate] = Field(default_factory=list)


class SceneSfxResult(BaseModel):
    scene_id: str
    query: str
    primary: CastCandidate | None = None
    alternatives: list[CastCandidate] = Field(default_factory=list)


class CastReport(BaseModel):
    series_id: str
    language: str
    voice_provider: str = "elevenlabs"
    characters: list[CharacterCastResult]
    scenes: list[SceneSfxResult]
    index_name: str
    endpoint_name: str
