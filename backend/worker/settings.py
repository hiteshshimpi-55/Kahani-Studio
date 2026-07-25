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
    script_audio_job,
)

async def ping_job(ctx: dict) -> dict:
    """Smoke-test job — proves worker + Redis queue are wired."""
    marker = f"{settings.data_dir}/worker_ping.txt"
    with open(marker, "a", encoding="utf-8") as f:
        f.write("ping\n")
    return {"ok": True, "marker": marker}


async def audience_sim_job(ctx: dict, sim_run_id: str, payload: dict) -> dict:
    """Run the full audience simulation pipeline for an episode.

    Called via: redis.enqueue_job("audience_sim_job", sim_run_id, payload)
    payload keys: script, part_count, genre, language, persona_count
    """
    from sqlalchemy import update
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.db.session import AsyncSessionLocal
    from app.repository.models.audience import SimPatch, SimRun, SimRunStatus
    from app.worker.audience.pipeline import run_audience_simulation

    async with AsyncSessionLocal() as session:
        session: AsyncSession

        # Mark as RUNNING
        await session.execute(
            update(SimRun).where(SimRun.id == sim_run_id).values(status=SimRunStatus.RUNNING)
        )
        await session.commit()

        try:
            result = run_audience_simulation(
                sim_run_id=sim_run_id,
                script=payload["script"],
                part_count=payload.get("part_count", 5),
                genre=payload.get("genre", "thriller"),
                language=payload.get("language", "hindi"),
                persona_count=payload.get("persona_count", 24),
            )

            # Persist results
            await session.execute(
                update(SimRun)
                .where(SimRun.id == sim_run_id)
                .values(
                    status=SimRunStatus.COMPLETED,
                    engagement_report=result.engagement.model_dump(),
                    audit_result=result.audit.model_dump(),
                    persona_count=result.engagement.persona_count,
                )
            )

            # Persist patches
            for patch in result.patches.patches:
                db_patch = SimPatch(
                    sim_run_id=sim_run_id,
                    beat_id=patch.beat_id,
                    part=patch.part,
                    patch_type=patch.patch_type,
                    rationale=patch.rationale,
                    suggested_text=patch.suggested_text,
                    expected_delta=patch.expected_delta,
                )
                session.add(db_patch)

            await session.commit()
            return {"ok": True, "sim_run_id": sim_run_id, "patches": len(result.patches.patches)}

        except Exception as exc:
            await session.execute(
                update(SimRun)
                .where(SimRun.id == sim_run_id)
                .values(status=SimRunStatus.FAILED, error=str(exc))
            )
            await session.commit()
            return {"ok": False, "sim_run_id": sim_run_id, "error": str(exc)}

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

async def on_startup(ctx: dict) -> None:
    from app.agents.graph.checkpointer import init_checkpointer

    await init_checkpointer()


async def on_shutdown(ctx: dict) -> None:
    from app.agents.graph.checkpointer import shutdown_checkpointer

    await shutdown_checkpointer()


class WorkerSettings:
    functions = [
        ping_job,
        audience_sim_job,
        index_attachment_job,
        delete_attachment_index_job,
        project_run_job,
        script_audio_job,
        tts_synthesize_job,
        render_visual_track,
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 5
    on_startup = on_startup
    on_shutdown = on_shutdown
