"""API routes for audience simulation (PRD §6.9)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.schemas.audience.request import SimulateRequest
from app.schemas.audience.response import (
    EnqueueSimResponse,
    PatchDecisionRequest,
    PatchResponse,
    SimRunResponse,
    SimRunSummaryResponse,
)
from app.services.audience.service import AudienceService

router = APIRouter(prefix="/audience", tags=["audience"])


def _service(request: Request, db: AsyncSession) -> AudienceService:
    return AudienceService(redis=request.app.state.redis, db=db)


@router.post("/simulate", response_model=EnqueueSimResponse)
async def enqueue_simulation(
    body: SimulateRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Enqueue a new audience simulation run for an episode."""
    service = _service(request, db)
    return await service.enqueue_simulation(body)


@router.get("/runs/{sim_run_id}", response_model=SimRunResponse)
async def get_sim_run(
    sim_run_id: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get full details of a simulation run (audit + engagement + patches)."""
    service = _service(request, db)
    result = await service.get_sim_run(sim_run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sim run not found")
    return result


@router.get("/episode/{episode_id}/runs", response_model=list[SimRunSummaryResponse])
async def list_sim_runs(
    episode_id: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all simulation runs for an episode."""
    service = _service(request, db)
    return await service.list_sim_runs(episode_id)


@router.patch("/patches/{patch_id}", response_model=PatchResponse)
async def decide_patch(
    patch_id: str,
    body: PatchDecisionRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Accept or reject a simulation patch."""
    if body.status not in ("ACCEPTED", "REJECTED"):
        raise HTTPException(status_code=422, detail="status must be ACCEPTED or REJECTED")
    service = _service(request, db)
    result = await service.decide_patch(patch_id, accepted=(body.status == "ACCEPTED"))
    if not result:
        raise HTTPException(status_code=404, detail="Patch not found")
    return result
