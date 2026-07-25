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


class RenderPreviewResponse(BaseModel):
    series_id: str
    title: str | None
    language: str
    model_id: str
    line_count: int
    sfx_cue_count: int
    sfx_clip_count: int
    voice_map: dict[str, str]
    preview_mp3: str | None = None
    stems: list[StemSummary]
    sfx_clips: list[SfxClipSummary]


@router.post("/preview", response_model=RenderPreviewResponse)
async def render_preview(body: RenderPreviewRequest) -> RenderPreviewResponse:
    """Render a short audiobook preview from a ScriptPackage.

    This is a heavy operation (multiple TTS + SFX API calls + ffmpeg).
    For production use, prefer the ARQ worker via ``/enqueue``.
    """
    result = await asyncio.to_thread(
        AudiobookService().render_preview,
        body.package,
        series_id=body.series_id,
        max_sec=body.max_sec,
        with_sfx=body.with_sfx,
    )
    return RenderPreviewResponse(
        series_id=result["series_id"],
        title=result["title"],
        language=result["language"],
        model_id=result["model_id"],
        line_count=result["line_count"],
        sfx_cue_count=result["sfx_cue_count"],
        sfx_clip_count=result.get("sfx_clip_count", 0),
        voice_map=result["voice_map"],
        preview_mp3=result.get("preview_mp3"),
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
