from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class StartRunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    session_id: str | None = None
    narration_config: dict | None = None
    # Part-by-part: one episode per run (part_count kept for API compat; ignored → 1)
    part_count: int | None = Field(default=1, ge=1, le=12)
    total_duration_sec: int | None = Field(default=90, ge=30, le=180)
    part_number: int | None = Field(default=None, ge=1, le=99)


class UpdateCharacterRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    role: str | None = None
    voice: str | None = None
    speech_patterns: str | None = None
    arc: str | None = None


class CreateCharacterRequest(BaseModel):
    character_key: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    role: str | None = None
    voice: str | None = None
    speech_patterns: str | None = None
    arc: str | None = None


class PinScriptRequest(BaseModel):
    pinned: bool = True


class UpdateScriptRequest(BaseModel):
    screenplay_md: str = Field(min_length=1)


class SaveDraftRequest(BaseModel):
    screenplay_md: str | None = None


class GenerateScriptAudioRequest(BaseModel):
    """Generate episode audio from a saved draft via ElevenLabs (or Sarvam)."""

    max_sec: float = Field(default=300.0, ge=30, le=600)
    voice_provider: str | None = Field(
        default=None,
        description="elevenlabs | sarvam — defaults to TTS_PROVIDER",
    )
    with_sfx: bool = True
    with_bed: bool = True


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
