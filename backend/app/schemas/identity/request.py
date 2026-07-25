from pydantic import BaseModel, Field

from app.schemas.visual.track import AspectRatio, DensityMode, StyleBible


class CreateSeriesRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    language: str = Field(default="hi", min_length=2, max_length=8)
    style_bible: StyleBible | None = None
    look: str = Field(
        default="cinematic thriller, muted teal-orange, photorealistic film still",
        max_length=500,
    )
    aspect_ratio: AspectRatio = AspectRatio.PORTRAIT
    density: DensityMode = DensityMode.SPARSE
    max_stills_per_part: int = Field(default=5, ge=1, le=40)


class CharacterSpec(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    role: str = Field(default="character", max_length=64)
    gender: str | None = None
    age_band: str | None = None
    identity_tokens: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Locked look description (age, ethnicity, hair, bone structure…)",
    )
    voice_provider_id: str | None = None
    expressions: list[str] = Field(
        default_factory=lambda: ["neutral", "fear", "whisper", "gasp"],
        description="Expression grid to generate after front portrait",
    )


class GenerateCharactersRequest(BaseModel):
    series_id: str
    characters: list[CharacterSpec] = Field(..., min_length=1)
    generate_images: bool = True


class LocationSpec(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(..., min_length=3, max_length=2000)
    kinds: list[str] = Field(default_factory=lambda: ["night"])


class GenerateLocationsRequest(BaseModel):
    series_id: str
    locations: list[LocationSpec] = Field(..., min_length=1)
    generate_images: bool = True
