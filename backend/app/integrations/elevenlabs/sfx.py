"""ElevenLabs Text-to-Sound-Effects integration."""

from __future__ import annotations

import logging

from elevenlabs.client import ElevenLabs

from app.errors.constants import ERROR_CODE_SFX_FAILED, ERROR_MSG_SFX_FAILED
from app.errors.exceptions import AppError

log = logging.getLogger(__name__)


def generate_sound_effect(
    client: ElevenLabs,
    *,
    prompt: str,
    duration_seconds: float | None = None,
    prompt_influence: float = 0.3,
) -> bytes:
    """Generate one SFX bed / Foley clip from a text prompt.

    ``duration_seconds`` defaults to *None* so ElevenLabs picks an
    appropriate length.  The caller should clamp to a sensible range
    (e.g. 8–22 s for ambience beds under narration).
    """
    try:
        raw = client.text_to_sound_effects.convert(
            text=prompt,
            duration_seconds=duration_seconds,
            prompt_influence=prompt_influence,
        )
        if isinstance(raw, (bytes, bytearray)):
            audio = bytes(raw)
        else:
            audio = b"".join(chunk for chunk in raw if chunk)
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            code=ERROR_CODE_SFX_FAILED,
            message=ERROR_MSG_SFX_FAILED,
            http_status_code=502,
            details=[f"prompt={prompt!r}: {exc}"],
        ) from exc

    if not audio:
        raise AppError(
            code=ERROR_CODE_SFX_FAILED,
            message=ERROR_MSG_SFX_FAILED,
            http_status_code=502,
            details=["empty audio response"],
        )

    log.info("sfx_generated prompt=%s bytes=%d", prompt[:60], len(audio))
    return audio
