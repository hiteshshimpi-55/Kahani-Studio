from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Iterator

from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs, ElevenLabs

from app.errors.constants import ERROR_CODE_TTS_FAILED, ERROR_MSG_TTS_FAILED
from app.errors.exceptions import AppError
from app.integrations.elevenlabs.types import TtsConvertRequest, TtsConvertResult, VoiceSettingsParams

log = logging.getLogger(__name__)


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
    parts: list[bytes] = []
    for chunk in chunks:
        if not chunk:
            continue
        if isinstance(chunk, (bytes, bytearray)):
            parts.append(bytes(chunk))
        else:
            try:
                parts.append(bytes(chunk))
            except Exception:
                log.warning("elevenlabs_skip_non_bytes_chunk type=%s", type(chunk))
    return b"".join(parts)


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
        log.exception(
            "elevenlabs_tts_failed voice_id=%s model_id=%s chars=%d",
            request.voice_id,
            request.model_id,
            len(request.text or ""),
        )
        raise AppError(
            code=ERROR_CODE_TTS_FAILED,
            message=ERROR_MSG_TTS_FAILED,
            http_status_code=502,
            details=[str(exc)],
        ) from exc

    if not audio:
        # Retry once with plain text (strip [tags] / *emphasis*) — v3 often
        # returns empty bytes for markdown-wrapped onomatopoeia.
        plain = _plain_tts_text(request.text)
        if plain and plain != request.text:
            log.warning(
                "elevenlabs_empty_retry voice_id=%s plain_chars=%d",
                request.voice_id,
                len(plain),
            )
            try:
                raw_retry = client.text_to_speech.convert(
                    voice_id=request.voice_id,
                    text=plain,
                    model_id=request.model_id,
                    output_format=request.output_format,
                    language_code=request.language_code,
                    voice_settings=_to_voice_settings(request.voice_settings),
                )
                audio = _collect_chunks(raw_retry)
            except Exception:
                log.exception("elevenlabs_empty_retry_failed")
        if not audio:
            raise AppError(
                code=ERROR_CODE_TTS_FAILED,
                message=ERROR_MSG_TTS_FAILED,
                http_status_code=502,
                details=[
                    "empty audio response",
                    f"voice_id={request.voice_id}",
                    f"text={request.text[:120]!r}",
                ],
            )

    return TtsConvertResult(
        audio=audio,
        voice_id=request.voice_id,
        model_id=request.model_id,
        output_format=request.output_format,
        character_count=len(request.text),
    )


def _plain_tts_text(text: str) -> str:
    """Strip v3 [direction] tags and markdown asterisks for a safe retry."""
    import re

    t = (text or "").strip()
    t = re.sub(r"^\[[^\]]+\]\s*", "", t)
    t = re.sub(r"^\*+([^*]+)\*+$", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    return t.strip()


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
        log.exception(
            "elevenlabs_tts_failed voice_id=%s model_id=%s chars=%d",
            request.voice_id,
            request.model_id,
            len(request.text or ""),
        )
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
