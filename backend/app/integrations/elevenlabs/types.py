from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VoiceSettingsParams:
    """Optional per-request voice settings (maps to ElevenLabs VoiceSettings)."""

    stability: float | None = None
    similarity_boost: float | None = None
    style: float | None = None
    use_speaker_boost: bool | None = None
    speed: float | None = None


@dataclass(frozen=True, slots=True)
class TtsConvertRequest:
    text: str
    voice_id: str
    model_id: str
    output_format: str
    language_code: str | None = None
    seed: int | None = None
    previous_text: str | None = None
    next_text: str | None = None
    previous_request_ids: list[str] | None = None
    next_request_ids: list[str] | None = None
    voice_settings: VoiceSettingsParams | None = None


@dataclass(frozen=True, slots=True)
class TtsConvertResult:
    audio: bytes
    voice_id: str
    model_id: str
    output_format: str
    character_count: int
