"""ARQ worker jobs for indexing and project LangGraph runs."""

from __future__ import annotations

import logging

from app.agents.graph.graph import RunCancelled, run_project_graph_cancellable
from app.core.db.session import AsyncSessionLocal
from app.integrations.databricks_ai_search import AISearchClient
from app.integrations.s3 import get_artifact_storage
from app.repository.projects import (
    AttachmentRepository,
    CharacterRepository,
    RunRepository,
    ScriptRepository,
)
from app.services.projects.chunking import chunk_text
from app.services.projects.continuity import (
    bible_characters,
    character_to_dict,
    script_to_continuity,
)
from app.services.projects.storage import (
    read_screenplay_artifact,
    write_run_package,
    write_run_screenplay,
)

logger = logging.getLogger(__name__)


async def index_attachment_job(ctx: dict, project_id: str, attachment_id: str) -> dict:
    async with AsyncSessionLocal() as session:
        repo = AttachmentRepository(session)
        row = await repo.get(attachment_id)
        if not row or row.project_id != project_id:
            return {"ok": False, "error": "attachment not found"}
        try:
            text = get_artifact_storage().get_text(row.storage_path)
            chunks = chunk_text(text)
            client = AISearchClient()
            client.upsert_chunks(
                project_id=project_id,
                attachment_id=attachment_id,
                filename=row.filename,
                chunks=chunks,
            )
            row.index_status = "indexed"
            await session.commit()
            return {"ok": True, "chunks": len(chunks)}
        except Exception as exc:
            logger.exception("index_attachment_job failed")
            row.index_status = "failed"
            await session.commit()
            return {"ok": False, "error": str(exc)}


async def delete_attachment_index_job(ctx: dict, project_id: str, attachment_id: str) -> dict:
    try:
        client = AISearchClient()
        client.delete_by_attachment(project_id=project_id, attachment_id=attachment_id)
        return {"ok": True}
    except Exception as exc:
        logger.exception("delete_attachment_index_job failed")
        return {"ok": False, "error": str(exc)}


async def project_run_job(ctx: dict, project_id: str, run_id: str) -> dict:
    async with AsyncSessionLocal() as session:
        runs = RunRepository(session)
        run = await runs.get(run_id)
        if not run or run.project_id != project_id:
            return {"ok": False, "error": "run not found"}

        if run.status == "cancelled":
            return {"ok": False, "cancelled": True}

        await runs.update_status(run_id, status="running")
        await session.commit()

        try:
            characters = CharacterRepository(session)
            scripts = ScriptRepository(session)
            cast_rows = await characters.list_for_project(project_id)
            series_cast = [character_to_dict(c) for c in cast_rows]

            script_rows = await scripts.list_for_project(project_id)
            continuity: list[dict] = []
            if script_rows:
                latest = script_rows[0]
                continuity.append(script_to_continuity(latest, is_latest=True))
                for row in script_rows[1:]:
                    if row.pinned:
                        continuity.append(script_to_continuity(row, is_latest=False))

            narration = run.narration_config or {}
            if run.part_number and run.part_number >= 1:
                part_number = int(run.part_number)
            else:
                part_number = (await scripts.max_part_number(project_id)) + 1

            # Prefer discovery.md written by chat pre-research (Tavily before enqueue).
            discovery_md = ""
            try:
                from app.services.projects.storage import run_object_prefix, runs_dir

                local_discovery = runs_dir(project_id, run_id) / "discovery.md"
                if local_discovery.is_file():
                    discovery_md = local_discovery.read_text(encoding="utf-8")
                else:
                    key = f"{run_object_prefix(project_id, run_id)}/discovery.md"
                    storage = get_artifact_storage()
                    if storage.exists(key):
                        discovery_md = storage.get_text(key) or ""
            except Exception:
                logger.exception("project_run_load_discovery_failed")

            if discovery_md.strip():
                logger.info(
                    "project_run_preloaded_discovery chars=%d run_id=%s",
                    len(discovery_md),
                    run_id,
                )

            initial = {
                "project_id": project_id,
                "run_id": run_id,
                "prompt": run.prompt,
                "narration_config": narration if isinstance(narration, dict) else {},
                "part_count": 1,
                "total_duration_sec": run.total_duration_sec or 90,
                "part_number": part_number,
                "series_cast": series_cast,
                "continuity_episodes": continuity,
                "retrieved_chunks": [],
                "discovery_md": discovery_md,
                "extraction": None,
                "crawl": None,
                "source_md": "",
                "script_package": None,
                "screenplay_md": None,
                "audio_result": None,
                "audio_s3_key": None,
                "cover_image_url": None,
                "errors": [],
            }

            async def _cancelled() -> bool:
                async with AsyncSessionLocal() as s2:
                    row = await RunRepository(s2).get(run_id)
                    return bool(row and row.status == "cancelled")

            try:
                thread_id = run.langgraph_thread_id or run_id
                if not run.langgraph_thread_id:
                    await runs.update_status(
                        run_id, status=run.status, langgraph_thread_id=thread_id
                    )
                    await session.commit()

                result = await run_project_graph_cancellable(
                    initial,
                    is_cancelled=_cancelled,
                    thread_id=thread_id,
                )
            except RunCancelled:
                await session.rollback()
                async with AsyncSessionLocal() as session2:
                    runs2 = RunRepository(session2)
                    await runs2.update_status(
                        run_id, status="cancelled", error="Stopped by user"
                    )
                    await session2.commit()
                return {"ok": False, "cancelled": True}

            if await _cancelled():
                await session.rollback()
                async with AsyncSessionLocal() as session2:
                    runs2 = RunRepository(session2)
                    await runs2.update_status(
                        run_id, status="cancelled", error="Stopped by user"
                    )
                    await session2.commit()
                return {"ok": False, "cancelled": True}

            package = result.get("script_package") or {}
            screenplay = result.get("screenplay_md") or ""
            write_run_package(project_id, run_id, package if isinstance(package, dict) else {})
            write_run_screenplay(project_id, run_id, screenplay)

            if isinstance(package, dict):
                await characters.upsert_from_bible(project_id, bible_characters(package))

            from app.services.agent_render.service import is_headless_run
            from app.services.projects.stages import StagesService

            fresh = await runs.get(run_id)
            if fresh:
                await StagesService(session, redis=None).mark_script_pending(fresh)
                await session.flush()
                fresh = await runs.get(run_id) or fresh
                if is_headless_run(fresh):
                    redis = ctx.get("redis")
                    if redis is None:
                        logger.error(
                            "headless_auto_approve_skipped — redis missing in worker ctx"
                        )
                    else:
                        await StagesService(session, redis=redis).approve_stage(
                            project_id, run_id, "script"
                        )
                        logger.info(
                            "headless_script_auto_approved",
                            extra={"project_id": project_id, "run_id": run_id},
                        )
            else:
                await runs.update_status(run_id, status="succeeded", error=None)
            await session.commit()
            return {"ok": True}
        except Exception as exc:
            logger.exception("project_run_job failed")
            await session.rollback()
            async with AsyncSessionLocal() as session2:
                runs2 = RunRepository(session2)
                current = await runs2.get(run_id)
                if current and current.status == "cancelled":
                    return {"ok": False, "cancelled": True}
                await runs2.update_status(run_id, status="failed", error=str(exc)[:2000])
                await session2.commit()
            return {"ok": False, "error": str(exc)}


async def script_audio_job(
    ctx: dict,
    *,
    project_id: str,
    script_id: str,
    max_sec: float = 300.0,
    voice_provider: str = "elevenlabs",
    with_sfx: bool = True,
    with_bed: bool = True,
) -> dict:
    """Render draft screenplay to MP3 via ElevenLabs audiobook pipeline."""
    import asyncio

    from app.repository.projects import ScriptRepository
    from app.services.projects.audio import render_script_audio, write_audio_status

    async with AsyncSessionLocal() as session:
        scripts = ScriptRepository(session)
        script = await scripts.get(script_id)
        if not script or script.project_id != project_id:
            return {"ok": False, "error": "script not found"}

        screenplay = read_screenplay_artifact(script.screenplay_path)
        if not screenplay.strip():
            status = write_audio_status(
                script.storage_dir,
                {
                    "status": "failed",
                    "error": "Screenplay is empty",
                    "project_id": project_id,
                    "script_id": script_id,
                    "voice_provider": voice_provider,
                },
            )
            return {"ok": False, **status}

        status = await asyncio.to_thread(
            render_script_audio,
            project_id=project_id,
            script_id=script_id,
            storage_dir=script.storage_dir,
            package=script.package_json or {},
            screenplay_md=screenplay,
            max_sec=float(max_sec),
            voice_provider=voice_provider,
            with_sfx=with_sfx,
            with_bed=with_bed,
        )
        return {"ok": status.get("status") == "succeeded", **status}


async def generate_run_audio_job(
    ctx: dict,
    *,
    project_id: str,
    run_id: str,
    revision_notes: str | None = None,
    max_sec: float | None = None,
    voice_provider: str = "elevenlabs",
    with_sfx: bool = True,
    with_bed: bool = True,
) -> dict:
    """Render run screenplay → MP3, push to S3, mark audio pending_approval."""
    import asyncio
    import json
    from pathlib import Path

    from app.integrations.s3 import get_artifact_storage
    from app.services.audiobook.service import AudiobookService
    from app.services.projects.audio import package_with_screenplay
    from app.services.projects.stages import (
        ensure_stage_statuses,
        run_audio_key,
        run_audio_result_key,
    )
    from app.services.projects.storage import read_run_package, read_run_screenplay

    async with AsyncSessionLocal() as session:
        runs = RunRepository(session)
        run = await runs.get(run_id)
        if not run or run.project_id != project_id:
            return {"ok": False, "error": "run not found"}

        statuses = ensure_stage_statuses(run)
        statuses["audio"] = "generating"
        run.current_stage = "audio"
        run.stage_statuses = statuses
        run.audio_s3_key = None
        await session.commit()

        screenplay = read_run_screenplay(project_id, run_id)
        package = read_run_package(project_id, run_id)
        if revision_notes and revision_notes.strip():
            # Soft guidance for casting/tone — stored in package meta for mixers
            package = dict(package)
            package["revision_notes"] = revision_notes.strip()

        if not screenplay.strip():
            statuses["audio"] = "failed"
            run.stage_statuses = statuses
            run.error = "Screenplay is empty"
            await session.commit()
            return {"ok": False, "error": "Screenplay is empty"}

        duration = float(max_sec or run.total_duration_sec or 90)

        def _render() -> dict:
            pkg = package_with_screenplay(package, screenplay)
            result = AudiobookService().render_preview(
                pkg,
                series_id=f"run-{run_id}",
                max_sec=duration,
                with_sfx=with_sfx,
                with_bed=with_bed,
                voice_provider=voice_provider,
            )
            preview = result.get("preview_mp3")
            if not preview or not Path(str(preview)).is_file():
                raise RuntimeError("Audiobook render produced no MP3")

            storage = get_artifact_storage()
            audio_key = run_audio_key(project_id, run_id)
            storage.put_bytes(
                audio_key,
                Path(str(preview)).read_bytes(),
                content_type="audio/mpeg",
            )
            result_key = run_audio_result_key(project_id, run_id)
            payload = {
                **{k: v for k, v in result.items() if k != "timeline" or isinstance(v, list)},
                "preview_mp3": audio_key,
                "audio_s3_key": audio_key,
                "project_id": project_id,
                "run_id": run_id,
            }
            # Cap timeline size for JSON storage
            timeline = payload.get("timeline")
            if isinstance(timeline, list) and len(timeline) > 500:
                payload["timeline"] = timeline[:500]
            storage.put_text(
                result_key,
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                content_type="application/json",
            )
            return {"audio_key": audio_key, "result": payload}

        try:
            rendered = await asyncio.to_thread(_render)
            statuses = ensure_stage_statuses(run)
            statuses["audio"] = "pending_approval"
            run.stage_statuses = statuses
            run.current_stage = "audio"
            run.audio_s3_key = rendered["audio_key"]
            run.error = None
            await session.commit()
            return {"ok": True, "audio_key": rendered["audio_key"]}
        except Exception as exc:
            logger.exception("generate_run_audio_job failed")
            statuses = ensure_stage_statuses(run)
            statuses["audio"] = "failed"
            run.stage_statuses = statuses
            detail = str(exc)
            details = getattr(exc, "details", None)
            if isinstance(details, list) and details:
                detail = f"{detail}: {'; '.join(str(d) for d in details)}"
            run.error = detail[:2000]
            await session.commit()
            return {"ok": False, "error": detail}


async def generate_cover_art_job(
    ctx: dict,
    *,
    project_id: str,
    run_id: str,
    revision_notes: str | None = None,
    image_provider: str | None = None,
) -> dict:
    """Generate cover art from script (+ audio mood), push to S3."""
    import asyncio
    import json

    from app.agents.graph.nodes_visuals import generate_and_store_cover
    from app.integrations.s3 import get_artifact_storage
    from app.services.projects.stages import ensure_stage_statuses, run_audio_result_key
    from app.services.projects.storage import read_run_package

    async with AsyncSessionLocal() as session:
        runs = RunRepository(session)
        run = await runs.get(run_id)
        if not run or run.project_id != project_id:
            return {"ok": False, "error": "run not found"}

        statuses = ensure_stage_statuses(run)
        statuses["cover_art"] = "generating"
        run.current_stage = "cover_art"
        run.stage_statuses = statuses
        run.cover_s3_key = None
        await session.commit()

        package = read_run_package(project_id, run_id)
        audio_result: dict | None = None
        try:
            raw = get_artifact_storage().get_text(run_audio_result_key(project_id, run_id))
            data = json.loads(raw)
            if isinstance(data, dict):
                audio_result = data
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            audio_result = None

        try:
            cover_key = await asyncio.to_thread(
                generate_and_store_cover,
                project_id=project_id,
                run_id=run_id,
                package=package,
                audio_result=audio_result,
                revision_notes=revision_notes or run.revision_notes,
                image_provider=image_provider,
            )
            statuses = ensure_stage_statuses(run)
            statuses["cover_art"] = "pending_approval"
            run.stage_statuses = statuses
            run.current_stage = "cover_art"
            run.cover_s3_key = cover_key
            run.error = None
            await session.commit()
            return {"ok": True, "cover_key": cover_key}
        except Exception as exc:
            logger.exception("generate_cover_art_job failed")
            statuses = ensure_stage_statuses(run)
            statuses["cover_art"] = "failed"
            run.stage_statuses = statuses
            run.error = str(exc)[:2000]
            await session.commit()
            return {"ok": False, "error": str(exc)}


async def assemble_episode_job(ctx: dict, *, project_id: str, run_id: str) -> dict:
    """Write final manifest.json referencing all approved artifacts."""
    import json
    from datetime import datetime, timezone

    from app.integrations.s3 import get_artifact_storage
    from app.services.projects.stages import (
        ensure_stage_statuses,
        run_audio_result_key,
        run_manifest_key,
        run_object_prefix,
    )
    from app.services.projects.storage import read_run_package

    async with AsyncSessionLocal() as session:
        runs = RunRepository(session)
        run = await runs.get(run_id)
        if not run or run.project_id != project_id:
            return {"ok": False, "error": "run not found"}

        statuses = ensure_stage_statuses(run)
        statuses["assembly"] = "generating"
        run.current_stage = "assembly"
        run.stage_statuses = statuses
        await session.commit()

        prefix = run_object_prefix(project_id, run_id)
        package = read_run_package(project_id, run_id)
        audio_meta: dict = {}
        try:
            raw = get_artifact_storage().get_text(run_audio_result_key(project_id, run_id))
            data = json.loads(raw)
            if isinstance(data, dict):
                audio_meta = {
                    "duration_sec": data.get("duration_sec"),
                    "line_count": data.get("line_count"),
                    "sfx_clip_count": data.get("sfx_clip_count"),
                    "title": data.get("title"),
                }
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

        try:
            manifest = {
                "run_id": run_id,
                "project_id": project_id,
                "title": package.get("title") if isinstance(package, dict) else None,
                "script_key": f"{prefix}/screenplay.md",
                "package_key": f"{prefix}/script.json",
                "audio_key": run.audio_s3_key,
                "cover_key": run.cover_s3_key,
                "audio_result": audio_meta,
                "stage_statuses": {
                    "script": "approved",
                    "audio": "approved",
                    "cover_art": "approved",
                    "assembly": "approved",
                },
                "status": "complete",
                "assembled_at": datetime.now(timezone.utc).isoformat(),
            }
            manifest_key = run_manifest_key(project_id, run_id)
            get_artifact_storage().put_text(
                manifest_key,
                json.dumps(manifest, ensure_ascii=False, indent=2),
                content_type="application/json",
            )
            statuses = ensure_stage_statuses(run)
            statuses["assembly"] = "approved"
            run.stage_statuses = statuses
            run.current_stage = "complete"
            run.manifest_s3_key = manifest_key
            run.error = None
            await session.commit()
            return {"ok": True, "manifest_key": manifest_key}
        except Exception as exc:
            logger.exception("assemble_episode_job failed")
            statuses = ensure_stage_statuses(run)
            statuses["assembly"] = "failed"
            run.stage_statuses = statuses
            run.error = str(exc)[:2000]
            await session.commit()
            return {"ok": False, "error": str(exc)}


async def project_run_visuals_job(
    ctx: dict,
    *,
    project_id: str,
    run_id: str,
    image_provider: str | None = None,
) -> dict:
    """Seed run audio into visuals series → lookbook → scene stills (+ video)."""
    import asyncio
    import json

    from app.integrations.images import normalize_image_provider
    from app.integrations.s3 import get_artifact_storage
    from app.services.projects.audio import package_with_screenplay
    from app.services.projects.stages import (
        ensure_stage_statuses,
        run_audio_result_key,
        visuals_series_id,
    )
    from app.services.projects.storage import read_run_package, read_run_screenplay
    from app.services.visuals import VisualEpisodeService

    async with AsyncSessionLocal() as session:
        runs = RunRepository(session)
        run = await runs.get(run_id)
        if not run or run.project_id != project_id:
            return {"ok": False, "error": "run not found"}

        statuses = ensure_stage_statuses(run)
        statuses["visuals"] = "generating"
        run.stage_statuses = statuses
        run.error = None
        await session.commit()

        series_id = visuals_series_id(run_id)
        screenplay = read_run_screenplay(project_id, run_id)
        package = read_run_package(project_id, run_id)
        storage = get_artifact_storage()
        audio_s3_key = run.audio_s3_key

        def _render() -> dict:
            raw = storage.get_text(run_audio_result_key(project_id, run_id))
            audio_result = json.loads(raw)
            if not isinstance(audio_result, dict):
                raise RuntimeError("Invalid audio_result.json")

            audio_key = audio_s3_key or audio_result.get("audio_s3_key")
            if not audio_key:
                raise RuntimeError("No audio key for visuals")
            local_mp3 = storage.ensure_local(str(audio_key))
            audio_result = dict(audio_result)
            audio_result["preview_mp3"] = str(local_mp3)

            timeline = audio_result.get("timeline")
            if not isinstance(timeline, list) or not timeline:
                raise RuntimeError("audio_result has no timeline — regenerate audio")

            pkg = package_with_screenplay(package, screenplay)
            provider = normalize_image_provider(image_provider)
            visuals = VisualEpisodeService()

            lookbook = visuals.build_lookbook(
                pkg,
                audio_result,
                series_id=series_id,
                image_provider=provider,
                use_llm_director=True,
                force=False,
            )
            episode = visuals.render_episode(
                pkg,
                audio_result,
                series_id=series_id,
                image_provider=provider,
                use_llm_director=True,
                require_lookbook=True,
                force_lookbook=False,
                force_stills=False,
            )
            return {
                "lookbook_characters": len(lookbook.get("characters") or []),
                "shot_count": episode.get("shot_count"),
                "stills_rendered": episode.get("stills_rendered"),
                "video_url": episode.get("video_url"),
                "status": episode.get("status"),
            }

        try:
            result = await asyncio.to_thread(_render)
            statuses = ensure_stage_statuses(run)
            statuses["visuals"] = "approved"
            run.stage_statuses = statuses
            run.error = None
            await session.commit()
            return {"ok": True, "series_id": series_id, **result}
        except Exception as exc:
            logger.exception("project_run_visuals_job failed")
            statuses = ensure_stage_statuses(run)
            statuses["visuals"] = "failed"
            run.stage_statuses = statuses
            run.error = str(exc)[:2000]
            await session.commit()
            return {"ok": False, "error": str(exc)}
