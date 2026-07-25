from arq.connections import RedisSettings

from app.core.config import settings
from app.schemas.tts.request import SynthesizeSpeechRequest
from app.services.tts.service import TtsService
from app.workers.jobs import (
    assemble_episode_job,
    delete_attachment_index_job,
    generate_cover_art_job,
    generate_run_audio_job,
    index_attachment_job,
    project_run_job,
    project_run_visuals_job,
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


async def visual_characters_job(ctx: dict, payload: dict) -> dict:
    """Lookbook step: same director plan as crime_v1, then character sheets only."""
    import asyncio

    from app.integrations.images import normalize_image_provider
    from app.services.audiobook.service import AudiobookService
    from app.services.visuals import VisualEpisodeService

    def _run() -> dict:
        series_id = payload.get("series_id", "visual_preview")
        package = payload["package"]
        provider = normalize_image_provider(payload.get("image_provider"))
        visuals = VisualEpisodeService()

        audio_result = None
        if bool(payload.get("reuse_audio", True)):
            audio_result = visuals.load_audio_result(series_id)
        if audio_result is None:
            audio_result = AudiobookService().render_preview(
                package,
                series_id=series_id,
                max_sec=float(payload.get("max_sec", 120.0)),
                concat=True,
                with_sfx=bool(payload.get("with_sfx", True)),
                with_bed=bool(payload.get("with_bed", True)),
                voice_provider=payload.get("voice_provider") or "elevenlabs",
            )

        return visuals.build_lookbook(
            package,
            audio_result,
            series_id=series_id,
            image_provider=provider,
            use_llm_director=bool(payload.get("use_llm_director", True)),
            force=bool(payload.get("force", False)),
        )

    return await asyncio.to_thread(_run)


async def visual_episode_job(ctx: dict, payload: dict) -> dict:
    """Visuals after audiobook (+ optional lookbook): director → stills → MP4."""
    import asyncio

    from app.integrations.images import normalize_image_provider
    from app.services.audiobook.service import AudiobookService
    from app.services.visuals import VisualEpisodeService

    def _run() -> dict:
        series_id = payload.get("series_id", "visual_preview")
        package = payload["package"]
        provider = normalize_image_provider(payload.get("image_provider"))
        visuals = VisualEpisodeService()

        audio_result = None
        if bool(payload.get("reuse_audio", True)):
            audio_result = visuals.load_audio_result(series_id)

        if audio_result is None:
            audio_result = AudiobookService().render_preview(
                package,
                series_id=series_id,
                max_sec=float(payload.get("max_sec", 120.0)),
                concat=True,
                with_sfx=bool(payload.get("with_sfx", True)),
                with_bed=bool(payload.get("with_bed", True)),
                voice_provider=payload.get("voice_provider") or "elevenlabs",
            )

        return visuals.render_episode(
            package,
            audio_result,
            series_id=series_id,
            use_llm_director=bool(payload.get("use_llm_director", True)),
            plan_only=bool(payload.get("plan_only", False)),
            image_provider=provider,
            require_lookbook=bool(payload.get("require_lookbook", True)),
            force_lookbook=bool(payload.get("force_lookbook", False)),
            force_stills=bool(payload.get("force_stills", False)),
        )

    return await asyncio.to_thread(_run)


async def on_startup(ctx: dict) -> None:
    from sqlalchemy import text

    from app.agents.graph.checkpointer import init_checkpointer
    from app.core.db.session import engine

    # Ensure production-stage columns exist (same alters as API lifespan)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "ALTER TABLE project_runs "
                    "ADD COLUMN IF NOT EXISTS current_stage VARCHAR(32)"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE project_runs "
                    "ADD COLUMN IF NOT EXISTS stage_statuses JSONB"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE project_runs "
                    "ADD COLUMN IF NOT EXISTS audio_s3_key VARCHAR(1024)"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE project_runs "
                    "ADD COLUMN IF NOT EXISTS cover_s3_key VARCHAR(1024)"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE project_runs "
                    "ADD COLUMN IF NOT EXISTS manifest_s3_key VARCHAR(1024)"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE project_runs "
                    "ADD COLUMN IF NOT EXISTS revision_notes TEXT"
                )
            )
    except Exception:
        pass

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
        generate_run_audio_job,
        generate_cover_art_job,
        assemble_episode_job,
        project_run_visuals_job,
        tts_synthesize_job,
        visual_characters_job,
        visual_episode_job,
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 5
    job_timeout = 1800  # visual episodes render many images
    on_startup = on_startup
    on_shutdown = on_shutdown
