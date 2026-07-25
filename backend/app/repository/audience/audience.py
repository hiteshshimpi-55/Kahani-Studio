"""Repository functions for audience simulation DB models."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repository.models.audience import PatchStatus, SimPatch, SimRun, SimRunStatus


async def create_sim_run(
    session: AsyncSession,
    *,
    episode_id: str,
    series_id: str,
    project_id: str | None = None,
) -> SimRun:
    """Create a new PENDING sim run."""
    row = SimRun(
        episode_id=episode_id,
        series_id=series_id,
        project_id=project_id,
        status=SimRunStatus.PENDING,
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


async def get_sim_run(session: AsyncSession, sim_run_id: str) -> SimRun | None:
    """Get a sim run with its patches loaded."""
    stmt = (
        select(SimRun)
        .where(SimRun.id == sim_run_id)
        .options(selectinload(SimRun.patches))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_sim_runs_for_episode(session: AsyncSession, episode_id: str) -> list[SimRun]:
    """List all sim runs for an episode, most recent first."""
    stmt = (
        select(SimRun)
        .where(SimRun.episode_id == episode_id)
        .order_by(SimRun.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_latest_sim_run_for_project(
    session: AsyncSession, project_id: str
) -> SimRun | None:
    """Return the most-recent sim run for a project (with patches loaded)."""
    stmt = (
        select(SimRun)
        .where(SimRun.project_id == project_id)
        .order_by(SimRun.created_at.desc())
        .options(selectinload(SimRun.patches))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_patch_status(
    session: AsyncSession,
    patch_id: str,
    status: PatchStatus,
) -> SimPatch | None:
    """Accept or reject a patch."""
    stmt = select(SimPatch).where(SimPatch.id == patch_id)
    result = await session.execute(stmt)
    patch = result.scalar_one_or_none()
    if patch:
        patch.status = status
        await session.flush()
        await session.refresh(patch)
    return patch
