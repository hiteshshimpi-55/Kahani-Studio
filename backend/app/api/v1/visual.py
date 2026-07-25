from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.schemas.visual.request import (
    PlanVisualRequest,
    PlanVisualResponse,
    RenderVisualRequest,
    RenderVisualResponse,
)
from app.services.jobs.service import JobsService
from app.services.visual.renderer import VisualRenderService

router = APIRouter(prefix="/visual", tags=["visual"])


@router.post("/plan", response_model=PlanVisualResponse)
async def plan_visual(
    body: PlanVisualRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlanVisualResponse:
    track = await VisualRenderService(db).plan(
        series_id=UUID(body.series_id),
        part=body.part,
        beats=body.beats,
        narration_sequence=body.narration_sequence,
        seq_timings=body.seq_timings,
        part_duration_sec=body.part_duration_sec,
        persist=body.persist,
    )
    return PlanVisualResponse(track=track)


@router.post("/render", response_model=RenderVisualResponse)
async def render_visual(
    body: RenderVisualRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RenderVisualResponse:
    if body.async_job:
        job = await JobsService(request.app.state.redis).enqueue_visual_render(
            {
                "series_id": body.series_id,
                "part": body.part,
                "max_shots": body.max_shots,
            }
        )
        return RenderVisualResponse(job_id=job.job_id, queued=True)

    track = await VisualRenderService(db).render_track(
        series_id=UUID(body.series_id),
        part=body.part,
        max_shots=body.max_shots,
    )
    return RenderVisualResponse(track=track, queued=False)
