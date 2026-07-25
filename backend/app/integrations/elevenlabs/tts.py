from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs, ElevenLabs

from app.errors.constants import ERROR_CODE_TTS_FAILED, ERROR_MSG_TTS_FAILED
from app.errors.exceptions import AppError
from app.integrations.elevenlabs.types import TtsConvertRequest, TtsConvertResult, VoiceSettingsParams


def _to_voice_settings(params: VoiceSettingsParams | None) -> VoiceSettings | None:
    if params is None:
        return None
    payload = {
        k: v
        for k, v in {
            "stability": params.stability,
            "similarity_boost": params.similarity_boost,
            "style": params.style,
            "use_speaker_boost": params.use_speaker_boost,
            "speed": params.speed,
        }.items()
        if v is not None
    }
    if not payload:
        return None
    return VoiceSettings(**payload)


def _collect_chunks(chunks: Iterator[bytes] | bytes) -> bytes:
    if isinstance(chunks, (bytes, bytearray)):
        return bytes(chunks)
    return b"".join(chunk for chunk in chunks if chunk)


async def _acollect_chunks(chunks: AsyncIterator[bytes] | bytes) -> bytes:
    if isinstance(chunks, (bytes, bytearray)):
        return bytes(chunks)
    parts: list[bytes] = []
    async for chunk in chunks:
        if chunk:
            parts.append(chunk)
    return b"".join(parts)


def convert_text_to_speech(
    client: ElevenLabs,
    request: TtsConvertRequest,
) -> TtsConvertResult:
    """Run sync TTS convert and return raw audio bytes."""
    try:
        raw = client.text_to_speech.convert(
            voice_id=request.voice_id,
            text=request.text,
            model_id=request.model_id,
            output_format=request.output_format,
            language_code=request.language_code,
            seed=request.seed,
            previous_text=request.previous_text,
            next_text=request.next_text,
            previous_request_ids=request.previous_request_ids,
            next_request_ids=request.next_request_ids,
            voice_settings=_to_voice_settings(request.voice_settings),
        )
        audio = _collect_chunks(raw)
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            code=ERROR_CODE_TTS_FAILED,
            message=ERROR_MSG_TTS_FAILED,
            http_status_code=502,
            details=[str(exc)],
        ) from exc

    if not audio:
        raise AppError(
            code=ERROR_CODE_TTS_FAILED,
            message=ERROR_MSG_TTS_FAILED,
            http_status_code=502,
            details=["empty audio response"],
        )

    return TtsConvertResult(
        audio=audio,
        voice_id=request.voice_id,
        model_id=request.model_id,
        output_format=request.output_format,
        character_count=len(request.text),
    )


async def aconvert_text_to_speech(
    client: AsyncElevenLabs,
    request: TtsConvertRequest,
) -> TtsConvertResult:
    """Run async TTS convert and return raw audio bytes."""
    try:
        raw = await client.text_to_speech.convert(
            voice_id=request.voice_id,
            text=request.text,
            model_id=request.model_id,
            output_format=request.output_format,
            language_code=request.language_code,
            seed=request.seed,
            previous_text=request.previous_text,
            next_text=request.next_text,
            previous_request_ids=request.previous_request_ids,
            next_request_ids=request.next_request_ids,
            voice_settings=_to_voice_settings(request.voice_settings),
        )
        audio = await _acollect_chunks(raw)
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            code=ERROR_CODE_TTS_FAILED,
            message=ERROR_MSG_TTS_FAILED,
            http_status_code=502,
            details=[str(exc)],
        ) from exc

    if not audio:
        raise AppError(
            code=ERROR_CODE_TTS_FAILED,
            message=ERROR_MSG_TTS_FAILED,
            http_status_code=502,
            details=["empty audio response"],
        )

    return TtsConvertResult(
        audio=audio,
        voice_id=request.voice_id,
        model_id=request.model_id,
        output_format=request.output_format,
        character_count=len(request.text),
    )
