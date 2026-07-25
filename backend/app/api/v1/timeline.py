"""ElevenLabs TTS for timeline dialogue clips."""

from __future__ import annotations

import logging
import math
import struct
import uuid
import wave
from io import BytesIO
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.config import settings

log = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["timeline"])

ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


class TtsClipRequest(BaseModel):
    clip_id: str
    text: str = Field(min_length=1, max_length=5000)
    voice_id: str = Field(min_length=1, max_length=128)


class TtsBatchRequest(BaseModel):
    clips: list[TtsClipRequest] = Field(max_length=80)


class TtsClipResult(BaseModel):
    clip_id: str
    audio_url: str
    duration_hint_sec: float | None = None
    stub: bool = False


class TtsBatchResponse(BaseModel):
    results: list[TtsClipResult]
    errors: list[dict[str, str]]


def _timeline_dir(project_id: str) -> Path:
    d = Path(settings.data_dir) / "projects" / project_id / "timeline"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _audio_url(project_id: str, filename: str) -> str:
    return f"/api/v1/projects/{project_id}/timeline/audio/{filename}"


def _stub_wav(text: str, duration_sec: float | None = None) -> bytes:
    """Generate a short tone WAV so the timeline works without an API key."""
    words = max(1, len(text.split()))
    dur = duration_sec or min(8.0, max(1.0, words / 2.6))
    sample_rate = 22050
    n = int(sample_rate * dur)
    freq = 220 + (hash(text) % 200)
    buf = BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n):
            t = i / sample_rate
            env = min(1.0, t * 8) * min(1.0, (dur - t) * 8)
            sample = int(12000 * env * math.sin(2 * math.pi * freq * t))
            frames += struct.pack("<h", sample)
        w.writeframes(frames)
    return buf.getvalue()


async def _elevenlabs_tts(text: str, voice_id: str) -> bytes:
    key = (settings.elevenlabs_api_key or "").strip()
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    url = ELEVEN_TTS_URL.format(voice_id=voice_id)
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        res = await client.post(
            url,
            headers={
                "xi-api-key": key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if res.status_code >= 400:
            detail = res.text[:400]
            raise RuntimeError(f"ElevenLabs {res.status_code}: {detail}")
        return res.content


async def _synthesize_one(project_id: str, req: TtsClipRequest) -> TtsClipResult:
    key = (settings.elevenlabs_api_key or "").strip()
    stub = False
    try:
        if key:
            audio = await _elevenlabs_tts(req.text, req.voice_id)
            ext = "mp3"
        else:
            audio = _stub_wav(req.text)
            ext = "wav"
            stub = True
    except Exception as e:
        log.warning("tts_failed clip=%s err=%s — using stub tone", req.clip_id, e)
        audio = _stub_wav(req.text)
        ext = "wav"
        stub = True

    filename = f"{req.clip_id}_{uuid.uuid4().hex[:8]}.{ext}"
    path = _timeline_dir(project_id) / filename
    path.write_bytes(audio)
    words = max(1, len(req.text.split()))
    hint = round(min(8.0, max(1.0, words / 2.6)), 2)
    return TtsClipResult(
        clip_id=req.clip_id,
        audio_url=_audio_url(project_id, filename),
        duration_hint_sec=hint,
        stub=stub,
    )


@router.post("/{project_id}/timeline/tts", response_model=TtsClipResult)
async def timeline_tts(project_id: str, body: TtsClipRequest) -> TtsClipResult:
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    return await _synthesize_one(project_id, body)


@router.post("/{project_id}/timeline/tts/batch", response_model=TtsBatchResponse)
async def timeline_tts_batch(project_id: str, body: TtsBatchRequest) -> TtsBatchResponse:
    results: list[TtsClipResult] = []
    errors: list[dict[str, str]] = []
    for clip in body.clips:
        try:
            results.append(await _synthesize_one(project_id, clip))
        except Exception as e:
            errors.append({"clip_id": clip.clip_id, "error": str(e)})
    return TtsBatchResponse(results=results, errors=errors)


@router.get("/{project_id}/timeline/audio/{filename}")
async def timeline_audio(project_id: str, filename: str) -> FileResponse:
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="invalid filename")
    path = _timeline_dir(project_id) / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="audio not found")
    media = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    return FileResponse(path, media_type=media)
