from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.config import settings
from app.services.health.service import HealthService

router = APIRouter(tags=["health"])
_health = HealthService()


@router.get("/health/live")
async def health_live():
    """Process liveness — no DB/Redis. Used by Docker healthchecks."""
    return {"status": "ok", "service": settings.app_name}


@router.get("/health")
async def health(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await _health.check(request, db)


@router.post("/health/ping-db")
async def ping_db(db: Annotated[AsyncSession, Depends(get_db)]):
    return await _health.ping_db(db)
