from uuid import UUID

from arq.connections import RedisSettings

from app.core.config import settings
from app.core.db.session import AsyncSessionLocal
from app.schemas.tts.request import SynthesizeSpeechRequest
from app.services.tts.service import TtsService
from app.services.visual.renderer import VisualRenderService
from app.workers.jobs import (
    delete_attachment_index_job,
    index_attachment_job,
    project_run_job,
)


async def ping_job(ctx: dict) -> dict:
    """Smoke-test job — proves worker + Redis queue are wired."""
    marker = f"{settings.data_dir}/worker_ping.txt"
    with open(marker, "a", encoding="utf-8") as f:
        f.write("ping\n")
    return {"ok": True, "marker": marker}


async def tts_synthesize_job(ctx: dict, payload: dict) -> dict:
    """Generate one VO stem via ElevenLabs and write under DATA_DIR/tts/."""
    request = SynthesizeSpeechRequest.model_validate(payload)
    result = TtsService().synthesize(request)
    return result.model_dump(mode="json")


async def render_visual_track(ctx: dict, payload: dict) -> dict:
    """Render planned VisualTrack stills for a series part (PuLID + Flux)."""
    series_id = UUID(payload["series_id"])
    part = int(payload.get("part") or 1)
    max_shots = payload.get("max_shots")
    async with AsyncSessionLocal() as session:
        try:
            track = await VisualRenderService(session).render_track(
                series_id=series_id,
                part=part,
                max_shots=max_shots,
            )
            await session.commit()
            return track.model_dump(mode="json")
        except Exception:
            await session.rollback()
            raise


class WorkerSettings:
    functions = [
        ping_job,
        index_attachment_job,
        delete_attachment_index_job,
        project_run_job,
        tts_synthesize_job,
        render_visual_track,
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 5
