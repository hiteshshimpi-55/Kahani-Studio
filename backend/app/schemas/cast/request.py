from pydantic import BaseModel, Field


class CastCharacter(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    role: str = Field(default="character", description="narrator | character")
    age_band: str | None = None
    gender: str | None = None
    traits: list[str] = Field(default_factory=list)
    casting_query: str = Field(..., min_length=3, max_length=1000)


class CastScene(BaseModel):
    scene_id: str = Field(..., min_length=1, max_length=64)
    setting: str | None = None
    sfx_query: str = Field(..., min_length=3, max_length=1000)


class CastScript(BaseModel):
    series_id: str = Field(..., min_length=1, max_length=128)
    language: str = Field(default="hi", min_length=2, max_length=8)
    title: str | None = None
    characters: list[CastCharacter] = Field(..., min_length=1)
    scenes: list[CastScene] = Field(default_factory=list)
