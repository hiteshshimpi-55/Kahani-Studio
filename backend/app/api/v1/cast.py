from fastapi import APIRouter
import asyncio

from app.schemas.cast.request import CastScript
from app.schemas.cast.response import CastReport
from app.services.cast.service import CastService

router = APIRouter(prefix="/cast", tags=["cast"])


@router.post("/recommend", response_model=CastReport)
async def recommend_cast(body: CastScript) -> CastReport:
    """Recommend top-2 ElevenLabs voices per character and SFX prompts per scene."""
    return await asyncio.to_thread(CastService().recommend, body)
