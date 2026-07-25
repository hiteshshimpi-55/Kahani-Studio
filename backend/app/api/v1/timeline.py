from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.schemas.visual.response import TimelineResponse
from app.services.visual.renderer import VisualRenderService

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/{series_id}/{part}", response_model=TimelineResponse)
async def get_timeline(
    series_id: UUID,
    part: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimelineResponse:
    data = await VisualRenderService(db).get_timeline(series_id, part)
    return TimelineResponse.model_validate(data)
