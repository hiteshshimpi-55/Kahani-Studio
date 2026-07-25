"""Sarvam AI Bulbul v3 TTS — synchronous REST wrapper.

Response is base64-encoded audio in ``response.audios``.
We decode and return raw bytes (WAV by default, configurable).

Emotion / delivery notes
------------------------
Unlike ElevenLabs v3, Bulbul does **not** support ``[direction]`` audio tags
or SSML. Expressiveness is controlled by:

- ``temperature`` (0.01–1.0, default 0.6): higher → more prosodic variation
  and emotional colour. Storytelling / character speech wants 0.75–0.95.
- ``pace`` (0.5–2.0): speaking rate only.

Always pass an explicit temperature for audiobook lines or delivery will
sound flat compared to ElevenLabs.
"""

from __future__ import annotations

import base64
import logging

from sarvamai import SarvamAI

from app.integrations.sarvam.constants import SARVAM_MODEL_ID

log = logging.getLogger(__name__)


def sarvam_tts(
    client: SarvamAI,
    *,
    text: str,
    speaker: str = "shubh",
    language_code: str = "hi-IN",
    pace: float = 1.0,
    temperature: float = 0.8,
    sample_rate: int = 44100,
    output_format: str = "mp3",
) -> bytes:
    """Convert text to speech using Sarvam Bulbul v3.

    Returns decoded audio bytes (not base64).
    """
    # Clamp to API ranges
    pace = max(0.5, min(2.0, pace))
    temperature = max(0.01, min(1.0, temperature))

    kwargs: dict = {
        "text": text,
        "target_language_code": language_code,
        "model": SARVAM_MODEL_ID,
        "speaker": speaker,
        "pace": pace,
        "speech_sample_rate": sample_rate,
        "enable_preprocessing": True,
    }
    # temperature is bulbul:v3 only — pass explicitly for emotional range
    try:
        response = client.text_to_speech.convert(**kwargs, temperature=temperature)
    except TypeError:
        # Older SDK builds may not expose temperature as a kwarg
        log.warning("sarvam_sdk_no_temperature_kwarg — retrying without it")
        response = client.text_to_speech.convert(**kwargs)

    combined = "".join(response.audios)
    audio_bytes = base64.b64decode(combined)

    log.info(
        "sarvam_tts speaker=%s lang=%s pace=%.2f temp=%.2f bytes=%d",
        speaker, language_code, pace, temperature, len(audio_bytes),
    )
    return audio_bytes
