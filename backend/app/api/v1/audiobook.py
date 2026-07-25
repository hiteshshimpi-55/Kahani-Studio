"""Audiobook preview render endpoint."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.audiobook.service import AudiobookService

router = APIRouter(prefix="/audiobook", tags=["audiobook"])


class RenderPreviewRequest(BaseModel):
    """Full ScriptPackage (from the script writer) + render options."""

    package: dict[str, Any] = Field(..., description="ScriptPackage JSON from the scripter")
    series_id: str = Field(default="preview", min_length=1, max_length=128)
    max_sec: float = Field(default=120.0, ge=5, le=600)
    with_sfx: bool = True
    with_bed: bool = Field(
        default=True,
        description="Loop a generated ambience bed under the dialogue (ducked)",
    )
    # Default Sarvam. Pass "elevenlabs" to cast + synthesize only with ElevenLabs.
    voice_provider: str = Field(
        default="elevenlabs",
        description="elevenlabs | sarvam — which voice catalog + TTS engine to use",
    )


class StemSummary(BaseModel):
    seq_id: str
    speaker: str
    voice_id: str
    spoken_text: str
    bytes: int


class SfxClipSummary(BaseModel):
    sfx_id: str
    cue: str
    bytes: int


class TimelineEvent(BaseModel):
    type: str
    seq_id: str
    t_start: float
    t_end: float
    speaker: str | None = None
    cue: str | None = None


class RenderPreviewResponse(BaseModel):
    series_id: str
    title: str | None
    language: str
    voice_provider: str
    model_id: str
    line_count: int
    sfx_cue_count: int
    sfx_clip_count: int
    voice_map: dict[str, str]
    provider_map: dict[str, str] = Field(default_factory=dict)
    bed_prompt: str | None = None
    preview_mp3: str | None = None
    duration_sec: float = 0.0
    timeline: list[TimelineEvent] = Field(default_factory=list)
    stems: list[StemSummary]
    sfx_clips: list[SfxClipSummary]


@router.post("/preview", response_model=RenderPreviewResponse)
async def render_preview(body: RenderPreviewRequest) -> RenderPreviewResponse:
    """Render a short audiobook preview from a ScriptPackage.

    ``voice_provider`` locks casting + TTS:
    - ``elevenlabs`` (default): ElevenLabs library voices + v3 emotion tags
    - ``sarvam``: native Hindi Sarvam Bulbul v3 voices

    SFX clips and ambience bed always use ElevenLabs sound generation.
    """
    result = await asyncio.to_thread(
        AudiobookService().render_preview,
        body.package,
        series_id=body.series_id,
        max_sec=body.max_sec,
        with_sfx=body.with_sfx,
        with_bed=body.with_bed,
        voice_provider=body.voice_provider,
    )
    return RenderPreviewResponse(
        series_id=result["series_id"],
        title=result["title"],
        language=result["language"],
        voice_provider=result.get("voice_provider") or body.voice_provider,
        model_id=result["model_id"],
        line_count=result["line_count"],
        sfx_cue_count=result["sfx_cue_count"],
        sfx_clip_count=result.get("sfx_clip_count", 0),
        voice_map=result["voice_map"],
        provider_map=result.get("provider_map") or {},
        bed_prompt=result.get("bed_prompt"),
        preview_mp3=result.get("preview_mp3"),
        duration_sec=float(result.get("duration_sec") or 0.0),
        timeline=[
            TimelineEvent(
                type=e["type"],
                seq_id=e["seq_id"],
                t_start=e["t_start"],
                t_end=e["t_end"],
                speaker=e.get("speaker"),
                cue=e.get("cue"),
            )
            for e in (result.get("timeline") or [])
        ],
        stems=[
            StemSummary(
                seq_id=s["seq_id"], speaker=s["speaker"],
                voice_id=s["voice_id"], spoken_text=s["spoken_text"],
                bytes=s["bytes"],
            )
            for s in result["stems"]
        ],
        sfx_clips=[
            SfxClipSummary(
                sfx_id=c["sfx_id"], cue=c["cue"], bytes=c["bytes"],
            )
            for c in result.get("sfx_clips") or []
        ],
    )
