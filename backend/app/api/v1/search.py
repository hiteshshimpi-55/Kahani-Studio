from fastapi import APIRouter
import asyncio

from app.schemas.search.request import VectorSearchRequest
from app.schemas.search.response import VectorSearchResponse
from app.services.search.service import VectorSearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/vector", response_model=VectorSearchResponse)
async def vector_search(body: VectorSearchRequest) -> VectorSearchResponse:
    """Query Databricks AI Search (Vector Search) index."""
    return await asyncio.to_thread(VectorSearchService().search, body)
