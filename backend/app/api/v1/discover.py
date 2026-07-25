from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.discover.response import TrendingTopicsResponse
from app.services.discover.service import DiscoverService

router = APIRouter(prefix="/discover", tags=["discover"])


@router.get("/trending", response_model=TrendingTopicsResponse)
async def trending_topics(
    region: str = Query("IN", description="ISO 3166-1 alpha-2 country code"),
    state: str | None = Query(None, description="State or province name for more local topics"),
    count: int = Query(8, ge=4, le=16, description="Number of topics to return"),
) -> TrendingTopicsResponse:
    """Return LLM-generated trending story topics for the given region/state."""
    return await DiscoverService().get_trending(region=region, state=state, count=count)
