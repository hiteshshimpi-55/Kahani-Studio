from fastapi import APIRouter, Request
import asyncio

from app.schemas.tts.request import SynthesizeSpeechRequest
from app.schemas.tts.response import EnqueueSynthesizeResponse, SynthesizeSpeechResponse
from app.services.tts.service import TtsService

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("/synthesize", response_model=SynthesizeSpeechResponse)
async def synthesize_speech(body: SynthesizeSpeechRequest) -> SynthesizeSpeechResponse:
    """Synchronous TTS — useful for short smoke tests. Prefer /enqueue for parts."""
    return await asyncio.to_thread(TtsService().synthesize, body)


@router.post("/enqueue", response_model=EnqueueSynthesizeResponse)
async def enqueue_synthesize(
    body: SynthesizeSpeechRequest,
    request: Request,
) -> EnqueueSynthesizeResponse:
    """Queue TTS on the ARQ worker (writes stem under /data/tts/...)."""
    job = await request.app.state.redis.enqueue_job(
        "tts_synthesize_job",
        body.model_dump(mode="json"),
    )
    return EnqueueSynthesizeResponse(
        job_id=job.job_id if job else None,
        queued=True,
        series_id=body.series_id,
        seq_id=body.seq_id,
    )
