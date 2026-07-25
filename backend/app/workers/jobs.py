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
                "source_md": "",
                "script_package": None,
                "screenplay_md": None,
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
