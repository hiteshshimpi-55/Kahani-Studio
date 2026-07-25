"""Visual episode routes — characters (lookbook) then full video render.

Image/video blobs live in S3; Postgres ``visual_media_assets`` maps them.
APIs return presigned URLs, not local disk paths.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.integrations.images import normalize_image_provider
from app.services.visuals import VisualEpisodeService

router = APIRouter(prefix="/visuals", tags=["visuals"])

ImageProviderOpt = Literal["chatgpt", "openai", "gemini"]


class BuildCharactersRequest(BaseModel):
    """Step 2 after audiobook: same director plan as crime_v1, lookbook images only."""

    package: dict[str, Any] = Field(description="ScriptPackage JSON (same as audiobook)")
    series_id: str = Field(
        default="visual_preview",
        description="Same series_id as the audiobook preview",
    )
    image_provider: ImageProviderOpt | None = Field(
        default=None,
        description='Image engine: "chatgpt" | "openai" (default) | "gemini". Omit → ChatGPT.',
    )
    reuse_audio: bool = True
    use_llm_director: bool = True
    force: bool = Field(
        default=False,
        description="Regenerate lookbook images even if files already exist",
    )
    max_sec: float = 120.0
    with_sfx: bool = True
    with_bed: bool = True
    voice_provider: str = "elevenlabs"


class RenderVisualEpisodeRequest(BaseModel):
    """Step 3: director shots + scene stills + MP4 (reuses locked lookbook).

    Typical flow:
      1. POST /api/v1/audiobook/preview
      2. POST /api/v1/visuals/characters
      3. POST /api/v1/visuals/render
    """

    package: dict[str, Any] = Field(description="ScriptPackage JSON (same as audiobook)")
    series_id: str = Field(
        default="visual_preview",
        description="Must match audiobook + characters series_id",
    )
    image_provider: ImageProviderOpt | None = Field(
        default=None,
        description='Image engine: "chatgpt" | "openai" (default) | "gemini". Omit → ChatGPT.',
    )
    reuse_audio: bool = Field(
        default=True,
        description="Reuse saved audiobook timeline/preview for this series_id",
    )
    require_lookbook: bool = Field(
        default=True,
        description="Fail if characters/lookbook not built yet (recommended)",
    )
    max_sec: float = 120.0
    use_llm_director: bool = True
    plan_only: bool = False
    force_lookbook: bool = Field(
        default=False,
        description="Regenerate character lookbook sheets (and re-plan with vector RAG)",
    )
    force_stills: bool = Field(
        default=False,
        description="Regenerate scene stills even if cached in S3/local",
    )
    with_sfx: bool = True
    with_bed: bool = True
    voice_provider: str = "elevenlabs"


@router.post("/characters")
async def build_characters(body: BuildCharactersRequest, request: Request):
    """Enqueue lookbook generation (locked character reference sheets).

    Poll GET /api/v1/visuals/{series_id}/characters until status=ready.
    """
    provider = normalize_image_provider(body.image_provider)
    payload = body.model_dump()
    payload["image_provider"] = provider
    job = await request.app.state.redis.enqueue_job("visual_characters_job", payload)
    return {
        "job_id": job.job_id if job else None,
        "series_id": body.series_id,
        "image_provider": provider,
        "queued": True,
        "poll": f"/api/v1/visuals/{body.series_id}/characters",
    }


@router.get("/{series_id}/characters")
async def get_characters(series_id: str):
    """Return locked character looks + lookbook S3 URLs."""
    payload = VisualEpisodeService().characters_status(series_id)
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail=f"no characters for '{series_id}' — POST /api/v1/visuals/characters first",
        )
    return payload


@router.post("/render")
async def render_visual_episode(body: RenderVisualEpisodeRequest, request: Request):
    """Enqueue full visual episode (shots → stills → MP4), reusing lookbook.

    Defaults to ChatGPT images when ``image_provider`` is omitted.
    """
    provider = normalize_image_provider(body.image_provider)
    payload = body.model_dump()
    payload["image_provider"] = provider
    job = await request.app.state.redis.enqueue_job("visual_episode_job", payload)
    return {
        "job_id": job.job_id if job else None,
        "series_id": body.series_id,
        "image_provider": provider,
        "queued": True,
        "poll": f"/api/v1/visuals/{body.series_id}",
    }


@router.get("/{series_id}")
async def get_visual_episode(series_id: str):
    """Current state of a visual episode: plan, lookbook, stills, video (S3 URLs)."""
    payload = VisualEpisodeService().episode_status(series_id)
    if payload.get("status") == "missing":
        raise HTTPException(
            status_code=404,
            detail=(
                f"no visual episode for series '{series_id}' — "
                "audiobook → POST /visuals/characters → POST /visuals/render"
            ),
        )
    return payload
