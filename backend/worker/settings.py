from arq.connections import RedisSettings

from app.core.config import settings
from app.schemas.tts.request import SynthesizeSpeechRequest
from app.services.tts.service import TtsService
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
        )

    return await asyncio.to_thread(_run)


class WorkerSettings:
    functions = [
        ping_job,
        index_attachment_job,
        delete_attachment_index_job,
        project_run_job,
        tts_synthesize_job,
        visual_characters_job,
        visual_episode_job,
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 5
    job_timeout = 1800  # visual episodes render many images
