from fastapi import APIRouter
import asyncio

from app.schemas.cast.request import CastScript
from app.schemas.cast.response import CastReport
from app.services.cast.service import CastService

router = APIRouter(prefix="/cast", tags=["cast"])


@router.post("/recommend", response_model=CastReport)
async def recommend_cast(body: CastScript) -> CastReport:
    """Recommend voices per character + SFX prompts per scene.

    Set ``voice_provider`` on the body:
    - ``sarvam`` (default) — search only Sarvam Bulbul v3 speakers
    - ``elevenlabs`` — search only ElevenLabs library voices
    """
    return await asyncio.to_thread(CastService().recommend, body)
