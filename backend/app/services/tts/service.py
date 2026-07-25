from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.integrations.elevenlabs import (
    TtsConvertRequest,
    VoiceSettingsParams,
    convert_text_to_speech,
    get_elevenlabs_client,
)
from app.integrations.elevenlabs.constants import STEM_SUBDIR
from app.schemas.tts.request import SynthesizeSpeechRequest, VoiceSettingsBody
from app.schemas.tts.response import SynthesizeSpeechResponse


def _extension_for_format(output_format: str) -> str:
    if output_format.startswith("mp3"):
        return "mp3"
    if output_format.startswith("pcm") or output_format.startswith("wav"):
        return "wav"
    if output_format.startswith("opus"):
        return "opus"
    return "bin"


def _voice_settings(body: VoiceSettingsBody | None) -> VoiceSettingsParams | None:
    if body is None:
        return None
    return VoiceSettingsParams(
        stability=body.stability,
        similarity_boost=body.similarity_boost,
        style=body.style,
        use_speaker_boost=body.use_speaker_boost,
        speed=body.speed,
    )


def stem_path(*, series_id: str, seq_id: str, output_format: str) -> Path:
    ext = _extension_for_format(output_format)
    return Path(settings.data_dir) / STEM_SUBDIR / series_id / f"{seq_id}.{ext}"


class TtsService:
    """Generate VO stems under DATA_DIR/tts/{series_id}/{seq_id}.mp3."""

    def synthesize(self, request: SynthesizeSpeechRequest) -> SynthesizeSpeechResponse:
        voice_id = request.voice_id or settings.elevenlabs_default_voice_id
        model_id = request.model_id or settings.elevenlabs_default_model_id
        output_format = request.output_format or settings.elevenlabs_default_output_format

        is_v3 = model_id == "eleven_v3"
        convert_req = TtsConvertRequest(
            text=request.text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format,
            language_code=request.language_code,
            seed=request.seed,
            previous_text=None if is_v3 else request.previous_text,
            next_text=None if is_v3 else request.next_text,
            voice_settings=_voice_settings(request.voice_settings),
        )

        client = get_elevenlabs_client()
        result = convert_text_to_speech(client, convert_req)

        out = stem_path(
            series_id=request.series_id,
            seq_id=request.seq_id,
            output_format=result.output_format,
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(result.audio)

        # Mirror stem to S3 when configured (local file kept).
        try:
            from app.services.visuals import artifacts as media

            media.publish(
                out,
                series_id=request.series_id,
                kind=media.KIND_TTS,
                delete_local=False,
            )
        except Exception:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).exception(
                "tts_s3_publish_failed series=%s seq=%s", request.series_id, request.seq_id
            )

        relative = str(out.relative_to(settings.data_dir))
        return SynthesizeSpeechResponse(
            path=str(out),
            relative_path=relative,
            voice_id=result.voice_id,
            model_id=result.model_id,
            output_format=result.output_format,
            character_count=result.character_count,
            bytes=len(result.audio),
            series_id=request.series_id,
            seq_id=request.seq_id,
        )
