"""Visual episode routes — characters (lookbook) then full video render."""

from __future__ import annotations

import json
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
    """Return locked character looks + lookbook image paths."""
    service = VisualEpisodeService()
    plan = service.load_characters(series_id)
    lookbook_dir = service.out_dir(series_id) / "lookbook"
    files = (
        sorted(p.name for p in lookbook_dir.glob("*.png"))
        if lookbook_dir.exists()
        else []
    )
    if plan is None and not files:
        raise HTTPException(
            status_code=404,
            detail=f"no characters for '{series_id}' — POST /api/v1/visuals/characters first",
        )
    characters = []
    if plan:
        characters = [
            {
                "id": c.id,
                "name": c.name,
                "appearance": c.appearance,
                "wardrobe": c.wardrobe,
                "facing": c.facing,
                "reference_image": c.reference_image,
            }
            for c in plan.characters
        ]
    return {
        "series_id": series_id,
        "status": "ready" if characters and files else ("pending" if not characters else "partial"),
        "characters": characters,
        "style": plan.style.model_dump() if plan else None,
        "lookbook_files": files,
        "lookbook": {c["id"]: c.get("reference_image") for c in characters},
    }


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
    """Current state of a visual episode: plan, lookbook, stills, video."""
    service = VisualEpisodeService()
    out_dir = service.out_dir(series_id)
    plan_path = out_dir / "plan.json"
    video = out_dir / "episode.mp4"
    stills = (
        sorted(p.name for p in (out_dir / "shots").glob("*.png"))
        if (out_dir / "shots").exists()
        else []
    )
    lookbook = (
        sorted(p.name for p in (out_dir / "lookbook").glob("*.png"))
        if (out_dir / "lookbook").exists()
        else []
    )
    chars = service.load_characters(series_id)

    if not plan_path.exists() and not video.exists() and chars is None and not lookbook:
        audio = service.load_audio_result(series_id)
        if audio is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"no visual episode for series '{series_id}' — "
                    "audiobook → POST /visuals/characters → POST /visuals/render"
                ),
            )
        return {
            "series_id": series_id,
            "status": "pending",
            "plan": None,
            "lookbook": lookbook,
            "stills": stills,
            "video_path": None,
            "characters_ready": False,
            "duration_sec": audio.get("duration_sec"),
        }

    return {
        "series_id": series_id,
        "status": "ready" if video.exists() else ("characters_ready" if chars and not plan_path.exists() else "planned"),
        "plan": json.loads(plan_path.read_text()) if plan_path.exists() else None,
        "lookbook": lookbook,
        "stills": stills,
        "video_path": str(video) if video.exists() else None,
        "shot_count": len(stills),
        "characters_ready": bool(chars and chars.characters),
    }
