from pydantic import BaseModel, Field


class VoiceSettingsBody(BaseModel):
    stability: float | None = Field(default=None, ge=0, le=1)
    similarity_boost: float | None = Field(default=None, ge=0, le=1)
    style: float | None = Field(default=None, ge=0, le=1)
    use_speaker_boost: bool | None = None
    speed: float | None = Field(default=None, ge=0.7, le=1.2)


class SynthesizeSpeechRequest(BaseModel):
    """Synthesize one spoken unit (maps to a NarrationPlan seq_id)."""

    text: str = Field(..., min_length=1, max_length=10_000)
    voice_id: str | None = None
    model_id: str | None = None
    output_format: str | None = None
    language_code: str | None = Field(default=None, min_length=2, max_length=8)
    seed: int | None = Field(default=None, ge=0)
    previous_text: str | None = None
    next_text: str | None = None
    series_id: str = Field(default="scratch", min_length=1, max_length=128)
    seq_id: str = Field(default="line_001", min_length=1, max_length=128)
    voice_settings: VoiceSettingsBody | None = None
