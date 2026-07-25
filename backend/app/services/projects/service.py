from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from arq.connections import ArqRedis
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.chat_memory import append_turn, load_checkpoint_messages, messages_to_history_pairs
from app.agents.graph.checkpointer import get_checkpointer
from app.core.config import settings
from app.errors import AppError
from app.repository.models.project import (
    ChatSession,
    ProjectAttachment,
    ProjectCharacter,
    ProjectRun,
    Script,
)
from app.repository.projects import (
    AttachmentRepository,
    CharacterRepository,
    ChatSessionRepository,
    ProjectRepository,
    RunRepository,
    ScriptRepository,
)
from app.schemas.projects.request import (
    ChatMessageRequest,
    CreateCharacterRequest,
    CreateProjectRequest,
    GenerateScriptAudioRequest,
    PinScriptRequest,
    RejectStageRequest,
    SaveDraftRequest,
    StartRunRequest,
    UpdateCharacterRequest,
    UpdateScriptRequest,
)
from app.schemas.projects.response import (
    AttachmentResponse,
    CharacterResponse,
    ChatHistoryItem,
    ChatMessageResponse,
    ChatSessionResponse,
    ProjectResponse,
    RunArtifactsResponse,
    RunProgressResponse,
    RunResponse,
    ScriptAudioStatusResponse,
    ScriptDetailResponse,
    ScriptLatestResponse,
    ScriptSummaryResponse,
    StoryContextSummaryResponse,
)
from app.services.projects.stages import (
    StagesService,
    default_stage_statuses,
    ensure_stage_statuses,
)
from app.services.projects.continuity import (
    bible_characters,
    package_cliff,
    package_part_number,
    package_title,
)
from app.services.chat.checkpoint_history import build_session_chat_history
from app.services.chat.orchestrator import analyze_user_message
from app.integrations.s3.storage import get_artifact_storage
from app.services.projects.audio import (
    audio_file_path,
    read_audio_status,
    write_audio_status,
)
from app.services.projects.storage import (
    attachment_object_key,
    checksum_bytes,
    is_allowed_filename,
    read_run_package,
    read_run_screenplay,
    read_screenplay_artifact,
    run_object_prefix,
    write_run_screenplay,
    write_versioned_package,
    write_versioned_screenplay,
)
logger = logging.getLogger(__name__)

DEFAULT_NARRATION = {
    "pov": "third_limited",
    "cast_model": "multicast",
    "platform_style": "pocket_fm_serial",
    "soundscape": True,
    "narrators": [{"id": "NARRATOR", "voice_notes": "intense thriller narrator, measured suspense"}],
}

DEFAULT_EPISODE_DURATION_SEC = 90


class ProjectsService:
    def __init__(self, session: AsyncSession, redis: ArqRedis | None = None) -> None:
        self._session = session
        self._redis = redis
        self._projects = ProjectRepository(session)
        self._attachments = AttachmentRepository(session)
        self._sessions = ChatSessionRepository(session)
        self._runs = RunRepository(session)
        self._scripts = ScriptRepository(session)
        self._characters = CharacterRepository(session)

    async def create_project(self, body: CreateProjectRequest) -> ProjectResponse:
        row = await self._projects.create(name=body.name.strip(), description=body.description)
        return ProjectResponse.model_validate(row)

    async def list_projects(self) -> list[ProjectResponse]:
        rows = await self._projects.list_all()
        return [ProjectResponse.model_validate(r) for r in rows]

    async def get_project(self, project_id: str) -> ProjectResponse:
        row = await self._require_project(project_id)
        return ProjectResponse.model_validate(row)

    async def delete_project(self, project_id: str) -> None:
        row = await self._require_project(project_id)
        root = Path(settings.data_dir) / "projects" / project_id
        await self._projects.delete(row)
        if root.exists():
            import shutil

            shutil.rmtree(root, ignore_errors=True)

    async def list_sessions(self, project_id: str) -> list[ChatSessionResponse]:
        await self._require_project(project_id)
        await self._ensure_default_session(project_id)
        rows = await self._sessions.list_for_project(project_id)
        out: list[ChatSessionResponse] = []
        for s in rows:
            runs = await self._runs.list_for_project(project_id, session_id=s.id)
            out.append(
                ChatSessionResponse(
                    id=s.id,
                    project_id=s.project_id,
                    title=s.title,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    run_count=len(runs),
                )
            )
        return out

    async def reset_session(self, project_id: str) -> ChatSessionResponse:
        """Start a fresh chat session (previous sessions remain listed)."""
        await self._require_project(project_id)
        existing = await self._sessions.list_for_project(project_id)
        title = f"Session {len(existing) + 1}"
        row = await self._sessions.create(
            ChatSession(project_id=project_id, title=title)
        )
        return ChatSessionResponse(
            id=row.id,
            project_id=row.project_id,
            title=row.title,
            created_at=row.created_at,
            updated_at=row.updated_at,
            run_count=0,
        )

    async def _ensure_default_session(self, project_id: str) -> ChatSession:
        latest = await self._sessions.latest_for_project(project_id)
        if latest:
            await self._runs.assign_orphans(project_id, latest.id)
            return latest
        row = await self._sessions.create(
            ChatSession(project_id=project_id, title="Session 1")
        )
        await self._runs.assign_orphans(project_id, row.id)
        return row

    async def list_attachments(self, project_id: str) -> list[AttachmentResponse]:
        await self._require_project(project_id)
        rows = await self._attachments.list_for_project(project_id)
        return [AttachmentResponse.model_validate(r) for r in rows]

    async def upload_attachment(self, project_id: str, file: UploadFile) -> AttachmentResponse:
        await self._require_project(project_id)
        filename = file.filename or "upload.txt"
        if not is_allowed_filename(filename):
            raise AppError(
                code="VALIDATION_ERROR",
                message="Only .md, .txt, and .markdown files are supported",
                http_status_code=400,
            )
        data = await file.read()
        if not data:
            raise AppError(
                code="VALIDATION_ERROR",
                message="Empty file",
                http_status_code=400,
            )

        attachment = ProjectAttachment(
            project_id=project_id,
            filename=filename,
            content_type=file.content_type or "text/plain",
            size_bytes=len(data),
            storage_path="",  # set after id known
            checksum=checksum_bytes(data),
            index_status="pending",
        )
        attachment = await self._attachments.create(attachment)
        key = attachment_object_key(project_id, attachment.id, filename)
        get_artifact_storage().put_bytes(
            key,
            data,
            content_type=file.content_type or "text/plain",
        )
        attachment.storage_path = key
        await self._session.flush()
        await self._session.refresh(attachment)

        if self._redis is not None:
            try:
                await self._redis.enqueue_job(
                    "index_attachment_job",
                    project_id=project_id,
                    attachment_id=attachment.id,
                )
            except Exception:
                logger.exception("Failed to enqueue index_attachment_job")

        return AttachmentResponse.model_validate(attachment)

    async def delete_attachment(self, project_id: str, attachment_id: str) -> None:
        await self._require_project(project_id)
        row = await self._attachments.get(attachment_id)
        if not row or row.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Attachment not found", http_status_code=404)

        if self._redis is not None:
            try:
                await self._redis.enqueue_job(
                    "delete_attachment_index_job",
                    project_id=project_id,
                    attachment_id=attachment_id,
                )
            except Exception:
                logger.exception("Failed to enqueue delete_attachment_index_job")

        if row.storage_path:
            try:
                get_artifact_storage().delete(row.storage_path)
            except Exception:
                logger.exception("Failed to delete attachment object %s", row.storage_path)
        await self._attachments.delete(row)

    async def start_run(self, project_id: str, body: StartRunRequest) -> RunResponse:
        await self._require_project(project_id)
        narration = body.narration_config or DEFAULT_NARRATION

        if body.session_id:
            session = await self._sessions.get(body.session_id)
            if not session or session.project_id != project_id:
                raise AppError(code="NOT_FOUND", message="Session not found", http_status_code=404)
        else:
            session = await self._ensure_default_session(project_id)

        duration = body.total_duration_sec or DEFAULT_EPISODE_DURATION_SEC
        duration = max(30, min(180, int(duration)))
        if body.part_number and body.part_number >= 1:
            part_number = int(body.part_number)
        else:
            part_number = (await self._scripts.max_part_number(project_id)) + 1

        run = ProjectRun(
            project_id=project_id,
            session_id=session.id,
            prompt=body.prompt.strip(),
            status="queued",
            narration_config=narration,
            part_count=1,
            total_duration_sec=duration,
            part_number=part_number,
            current_stage="script",
            stage_statuses={**default_stage_statuses(), "script": "generating"},
        )
        run = await self._runs.create(run)
        # LangGraph thread id = run id (checkpoints keyed per generation run)
        await self._runs.update_status(
            run.id, status=run.status, langgraph_thread_id=run.id
        )
        run.langgraph_thread_id = run.id

        if self._redis is None:
            raise AppError(
                code="INTERNAL_ERROR",
                message="Redis unavailable",
                http_status_code=503,
            )

        job = await self._redis.enqueue_job(
            "project_run_job",
            project_id=project_id,
            run_id=run.id,
        )
        job_id = getattr(job, "job_id", None) or str(job)
        updated = await self._runs.update_status(run.id, status="queued", arq_job_id=job_id)
        return await self._run_response(updated or run)

    async def list_runs(
        self, project_id: str, *, session_id: str | None = None
    ) -> list[RunResponse]:
        await self._require_project(project_id)
        if session_id is None:
            session = await self._ensure_default_session(project_id)
            session_id = session.id
        else:
            session = await self._sessions.get(session_id)
            if not session or session.project_id != project_id:
                raise AppError(code="NOT_FOUND", message="Session not found", http_status_code=404)
        rows = await self._runs.list_for_project(project_id, session_id=session_id)
        return [await self._run_response(run) for run in rows]

    async def get_run(self, project_id: str, run_id: str) -> RunResponse:
        await self._require_project(project_id)
        run = await self._runs.get(run_id)
        if not run or run.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Run not found", http_status_code=404)
        return await self._run_response(run)

    async def save_run_as_draft(
        self,
        project_id: str,
        run_id: str,
        body: SaveDraftRequest | None = None,
    ) -> ScriptDetailResponse:
        await self._require_project(project_id)
        run = await self._runs.get(run_id)
        if not run or run.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Run not found", http_status_code=404)
        if run.status != "succeeded":
            raise AppError(
                code="VALIDATION_ERROR",
                message="Run must succeed before saving a draft",
                http_status_code=400,
            )

        existing = await self._scripts.get_for_run(run_id)
        if existing:
            if body and body.screenplay_md is not None:
                return await self.update_script(
                    project_id, existing.id, UpdateScriptRequest(screenplay_md=body.screenplay_md)
                )
            return ScriptDetailResponse(**(await self._script_detail(existing)).model_dump())

        screenplay = (body.screenplay_md if body and body.screenplay_md is not None else None) or read_run_screenplay(
            project_id, run_id
        )
        package = read_run_package(project_id, run_id)
        if not screenplay.strip():
            raise AppError(
                code="NOT_FOUND",
                message="No screenplay found for this run",
                http_status_code=404,
            )

        # Keep working copy in sync with what the user is saving
        write_run_screenplay(project_id, run_id, screenplay)

        version = await self._scripts.next_version(project_id)
        screenplay_key = write_versioned_screenplay(project_id, run_id, version, screenplay)
        write_versioned_package(project_id, run_id, version, package)
        storage_prefix = run_object_prefix(project_id, run_id)

        part_number = (
            package_part_number(package)
            or run.part_number
            or (await self._scripts.max_part_number(project_id)) + 1
        )
        script = Script(
            project_id=project_id,
            run_id=run_id,
            version=version,
            package_json=package,
            screenplay_path=screenplay_key,
            storage_dir=storage_prefix,
            part_number=part_number,
            pinned=False,
        )
        script = await self._scripts.create(script)
        await self._characters.upsert_from_bible(project_id, bible_characters(package))
        return ScriptDetailResponse(**(await self._script_detail(script)).model_dump())

    async def update_script(
        self, project_id: str, script_id: str, body: UpdateScriptRequest
    ) -> ScriptDetailResponse:
        await self._require_project(project_id)
        script = await self._scripts.get(script_id)
        if not script or script.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Script not found", http_status_code=404)

        get_artifact_storage().put_text(
            script.screenplay_path,
            body.screenplay_md,
            content_type="text/markdown; charset=utf-8",
        )
        # Keep run working copy in sync when present
        write_run_screenplay(project_id, script.run_id, body.screenplay_md)

        return ScriptDetailResponse(**(await self._script_detail(script)).model_dump())

    def _audio_status_response(
        self, script: Script, raw: dict | None
    ) -> ScriptAudioStatusResponse:
        if not raw:
            return ScriptAudioStatusResponse(
                script_id=script.id,
                project_id=script.project_id,
                status="idle",
            )
        return ScriptAudioStatusResponse(
            script_id=script.id,
            project_id=script.project_id,
            status=str(raw.get("status") or "idle"),
            error=raw.get("error"),
            audio_url=raw.get("audio_url"),
            voice_provider=raw.get("voice_provider"),
            line_count=raw.get("line_count"),
            sfx_clip_count=raw.get("sfx_clip_count"),
            title=raw.get("title"),
            updated_at=raw.get("updated_at"),
        )

    async def enqueue_script_audio(
        self,
        project_id: str,
        script_id: str,
        body: GenerateScriptAudioRequest | None = None,
    ) -> ScriptAudioStatusResponse:
        await self._require_project(project_id)
        script = await self._scripts.get(script_id)
        if not script or script.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Script not found", http_status_code=404)

        opts = body or GenerateScriptAudioRequest()
        provider = (opts.voice_provider or settings.tts_provider or "elevenlabs").strip().lower()
        if provider == "elevenlabs" and not (settings.elevenlabs_api_key or "").strip():
            raise AppError(
                code="VALIDATION_ERROR",
                message="ELEVENLABS_API_KEY is not set — add it to .env and restart",
                http_status_code=400,
            )
        if provider == "sarvam" and not (settings.sarvam_api_key or "").strip():
            raise AppError(
                code="VALIDATION_ERROR",
                message="SARVAM_API_KEY is not set — add it to .env and restart",
                http_status_code=400,
            )

        current = read_audio_status(script.storage_dir)
        if current and current.get("status") in ("queued", "running"):
            return self._audio_status_response(script, current)

        if self._redis is None:
            raise AppError(
                code="INTERNAL_ERROR",
                message="Redis unavailable — cannot enqueue audio job",
                http_status_code=503,
            )

        status = write_audio_status(
            script.storage_dir,
            {
                "status": "queued",
                "error": None,
                "audio_url": None,
                "voice_provider": provider,
                "project_id": project_id,
                "script_id": script_id,
            },
        )
        await self._session.commit()

        job = await self._redis.enqueue_job(
            "script_audio_job",
            project_id=project_id,
            script_id=script_id,
            max_sec=float(opts.max_sec),
            voice_provider=provider,
            with_sfx=bool(opts.with_sfx),
            with_bed=bool(opts.with_bed),
        )
        job_id = getattr(job, "job_id", None) or str(job)
        status = write_audio_status(
            script.storage_dir,
            {**status, "status": "queued", "arq_job_id": job_id},
        )
        return self._audio_status_response(script, status)

    async def get_script_audio_status(
        self, project_id: str, script_id: str
    ) -> ScriptAudioStatusResponse:
        await self._require_project(project_id)
        script = await self._scripts.get(script_id)
        if not script or script.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Script not found", http_status_code=404)
        raw = read_audio_status(script.storage_dir)
        # Heal URL if file exists but status missing url
        if raw and raw.get("status") == "succeeded" and not raw.get("audio_url"):
            from app.services.projects.audio import audio_file_key

            if get_artifact_storage().exists(audio_file_key(script.storage_dir)):
                raw = write_audio_status(
                    script.storage_dir,
                    {
                        **raw,
                        "audio_url": f"/api/v1/projects/{project_id}/scripts/{script_id}/audio/file",
                    },
                )
        return self._audio_status_response(script, raw)

    async def get_script_audio_file_path(self, project_id: str, script_id: str) -> Path:
        await self._require_project(project_id)
        script = await self._scripts.get(script_id)
        if not script or script.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Script not found", http_status_code=404)
        try:
            path = audio_file_path(script.storage_dir)
        except FileNotFoundError as exc:
            raise AppError(code="NOT_FOUND", message="Audio not ready", http_status_code=404) from exc
        if not path.is_file():
            raise AppError(code="NOT_FOUND", message="Audio not ready", http_status_code=404)
        return path

    async def post_chat_message(
        self, project_id: str, body: ChatMessageRequest
    ) -> ChatMessageResponse:
        """Clarify-first chat; messages persist in LangGraph checkpointer (session thread)."""
        await self._require_project(project_id)
        if body.session_id:
            session = await self._sessions.get(body.session_id)
            if not session or session.project_id != project_id:
                raise AppError(code="NOT_FOUND", message="Session not found", http_status_code=404)
        else:
            session = await self._ensure_default_session(project_id)

        message = body.message.strip()
        checkpointer = get_checkpointer()
        prior = await load_checkpoint_messages(checkpointer, session.id)
        history = messages_to_history_pairs(prior)

        attachments = await self._attachments.list_for_project(project_id)
        analysis = await analyze_user_message(
            user_message=message,
            history=history,
            attachment_count=len(attachments),
        )

        questions = analysis.get("questions") or []
        reply = str(analysis.get("reply") or "").strip()
        now = datetime.now(timezone.utc)

        # Natural language or clarifying questions — do not start generation
        if analysis.get("intent") != "generate" or not analysis.get("enough_context"):
            kind = "clarify" if analysis.get("needs_clarification") or questions else "reply"
            if questions:
                q_block = "\n".join(f"- {q}" for q in questions)
                content = f"{reply}\n\n{q_block}".strip() if reply else q_block
            else:
                content = reply
            _, assistant_id = await append_turn(
                checkpointer,
                session_id=session.id,
                user_text=message,
                assistant_text=content,
                kind=kind,
                questions=list(questions),
                analysis=analysis,
            )
            return ChatMessageResponse(
                id=assistant_id,
                role="assistant",
                content=content,
                kind=kind,
                created_at=now,
                questions=list(questions),
                session_id=session.id,
            )

        # Ready to generate — one episode per run
        brief = str(analysis.get("generation_brief") or message).strip()
        run_body = StartRunRequest(
            prompt=brief,
            session_id=session.id,
            part_count=1,
            total_duration_sec=DEFAULT_EPISODE_DURATION_SEC,
        )
        run = await self.start_run(project_id, run_body)
        content = reply or (
            "Writing the next episode now. You can stop anytime. "
            "When it finishes, save it as a draft to lock Cast and continuity."
        )
        _, assistant_id = await append_turn(
            checkpointer,
            session_id=session.id,
            user_text=message,
            assistant_text=content,
            kind="generating",
            run_id=run.id,
            questions=[],
            analysis=analysis,
        )
        return ChatMessageResponse(
            id=assistant_id,
            role="assistant",
            content=content,
            kind="generating",
            created_at=now,
            run_id=run.id,
            session_id=session.id,
            run=run,
        )

    async def list_chat_history(
        self, project_id: str, session_id: str | None = None
    ) -> list[ChatHistoryItem]:
        await self._require_project(project_id)
        if session_id:
            session = await self._sessions.get(session_id)
            if not session or session.project_id != project_id:
                raise AppError(code="NOT_FOUND", message="Session not found", http_status_code=404)
        else:
            session = await self._ensure_default_session(project_id)

        raw = await build_session_chat_history(get_checkpointer(), session.id)
        items: list[ChatHistoryItem] = []
        for row in raw:
            preview = None
            package = None
            draft_id = None
            is_draft = False
            run_status = None
            run_id = row.get("run_id")
            if run_id:
                run = await self._runs.get(str(run_id))
                if run:
                    run_status = run.status
                    rr = await self._run_response(run)
                    preview = rr.screenplay_md or rr.screenplay_preview
                    package = rr.package
                    draft_id = rr.draft_script_id
                    is_draft = rr.is_draft
            items.append(
                ChatHistoryItem(
                    id=str(row["id"]),
                    role=str(row["role"]),
                    content=str(row["content"]),
                    kind=str(row["kind"]),
                    created_at=row["created_at"],
                    run_id=str(run_id) if run_id else None,
                    questions=list(row.get("questions") or []),
                    script_preview=preview,
                    script_package=package,
                    draft_script_id=draft_id,
                    is_draft=is_draft,
                    run_status=run_status,
                )
            )
        return items

    async def cancel_run(self, project_id: str, run_id: str) -> RunResponse:
        await self._require_project(project_id)
        run = await self._runs.get(run_id)
        if not run or run.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Run not found", http_status_code=404)
        if run.status in ("succeeded", "failed", "cancelled"):
            return await self._run_response(run)
        updated = await self._runs.update_status(
            run_id, status="cancelled", error="Stopped by user"
        )
        return await self._run_response(updated or run)

    async def latest_script(self, project_id: str) -> ScriptLatestResponse:
        await self._require_project(project_id)
        script = await self._scripts.latest_for_project(project_id)
        if not script:
            raise AppError(code="NOT_FOUND", message="No script yet", http_status_code=404)
        return await self._script_detail(script)

    async def list_scripts(self, project_id: str) -> list[ScriptSummaryResponse]:
        await self._require_project(project_id)
        rows = await self._scripts.list_for_project(project_id)
        latest_id = rows[0].id if rows else None
        out: list[ScriptSummaryResponse] = []
        for script in rows:
            run = await self._runs.get(script.run_id)
            package = script.package_json if isinstance(script.package_json, dict) else {}
            title = package_title(package)
            prompt = (run.prompt if run else "") or ""
            snippet = prompt.strip().replace("\n", " ")
            if len(snippet) > 120:
                snippet = snippet[:117] + "…"
            out.append(
                ScriptSummaryResponse(
                    id=script.id,
                    project_id=script.project_id,
                    run_id=script.run_id,
                    version=script.version,
                    title=title,
                    prompt_snippet=snippet or None,
                    created_at=script.created_at,
                    part_number=script.part_number or package_part_number(package),
                    pinned=bool(script.pinned),
                    cliff_out=package_cliff(package),
                    is_latest_continuity=script.id == latest_id,
                )
            )
        return out

    async def pin_script(
        self, project_id: str, script_id: str, body: PinScriptRequest
    ) -> ScriptSummaryResponse:
        await self._require_project(project_id)
        script = await self._scripts.get(script_id)
        if not script or script.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Script not found", http_status_code=404)
        updated = await self._scripts.set_pinned(script_id, body.pinned)
        rows = await self.list_scripts(project_id)
        for row in rows:
            if row.id == script_id:
                return row
        # Fallback if list empty somehow
        package = (updated.package_json if updated else {}) or {}
        return ScriptSummaryResponse(
            id=script_id,
            project_id=project_id,
            run_id=script.run_id,
            version=script.version,
            title=package_title(package if isinstance(package, dict) else {}),
            prompt_snippet=None,
            created_at=script.created_at,
            part_number=script.part_number,
            pinned=body.pinned,
            cliff_out=package_cliff(package if isinstance(package, dict) else {}),
            is_latest_continuity=False,
        )

    async def list_characters(self, project_id: str) -> list[CharacterResponse]:
        await self._require_project(project_id)
        rows = await self._characters.list_for_project(project_id)
        return [CharacterResponse.model_validate(r) for r in rows]

    async def create_character(
        self, project_id: str, body: CreateCharacterRequest
    ) -> CharacterResponse:
        await self._require_project(project_id)
        key = body.character_key.strip().lower().replace(" ", "_")
        existing = await self._characters.get_by_key(project_id, key)
        if existing:
            raise AppError(
                code="VALIDATION_ERROR",
                message="Character key already exists",
                http_status_code=400,
            )
        row = ProjectCharacter(
            project_id=project_id,
            character_key=key,
            name=body.name.strip(),
            role=body.role,
            voice=body.voice,
            speech_patterns=body.speech_patterns,
            arc=body.arc,
        )
        row = await self._characters.create(row)
        return CharacterResponse.model_validate(row)

    async def update_character(
        self, project_id: str, character_id: str, body: UpdateCharacterRequest
    ) -> CharacterResponse:
        await self._require_project(project_id)
        row = await self._characters.get(character_id)
        if not row or row.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Character not found", http_status_code=404)
        if body.name is not None:
            row.name = body.name.strip()
        if body.role is not None:
            row.role = body.role
        if body.voice is not None:
            row.voice = body.voice
        if body.speech_patterns is not None:
            row.speech_patterns = body.speech_patterns
        if body.arc is not None:
            row.arc = body.arc
        await self._session.flush()
        await self._session.refresh(row)
        return CharacterResponse.model_validate(row)

    async def delete_character(self, project_id: str, character_id: str) -> None:
        await self._require_project(project_id)
        row = await self._characters.get(character_id)
        if not row or row.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Character not found", http_status_code=404)
        await self._characters.delete(row)

    async def story_context_summary(self, project_id: str) -> StoryContextSummaryResponse:
        await self._require_project(project_id)
        cast = await self._characters.list_for_project(project_id)
        docs = await self._attachments.list_for_project(project_id)
        scripts = await self._scripts.list_for_project(project_id)
        latest_pn = None
        if scripts:
            latest_pn = scripts[0].part_number or package_part_number(
                scripts[0].package_json if isinstance(scripts[0].package_json, dict) else {}
            )
        return StoryContextSummaryResponse(
            cast_count=len(cast),
            docs_count=len(docs),
            episode_count=len(scripts),
            latest_part_number=latest_pn,
        )

    async def get_script(self, project_id: str, script_id: str) -> ScriptDetailResponse:
        await self._require_project(project_id)
        script = await self._scripts.get(script_id)
        if not script or script.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Script not found", http_status_code=404)
        detail = await self._script_detail(script)
        return ScriptDetailResponse(**detail.model_dump())

    async def _script_detail(self, script) -> ScriptLatestResponse:
        screenplay = read_screenplay_artifact(script.screenplay_path)
        package = script.package_json if isinstance(script.package_json, dict) else {}
        return ScriptLatestResponse(
            id=script.id,
            project_id=script.project_id,
            run_id=script.run_id,
            version=script.version,
            package=package,
            screenplay_md=screenplay,
            created_at=script.created_at,
            part_number=script.part_number or package_part_number(package),
            pinned=bool(script.pinned),
            cliff_out=package_cliff(package),
            title=package_title(package),
        )

    async def approve_stage(self, project_id: str, run_id: str, stage: str) -> RunResponse:
        await self._require_project(project_id)
        run = await StagesService(self._session, self._redis).approve_stage(
            project_id, run_id, stage
        )
        return await self._run_response(run)

    async def reject_stage(
        self,
        project_id: str,
        run_id: str,
        stage: str,
        body: RejectStageRequest,
    ) -> RunResponse:
        await self._require_project(project_id)
        run = await StagesService(self._session, self._redis).reject_stage(
            project_id,
            run_id,
            stage,
            action=body.action,
            notes=body.notes,
        )
        return await self._run_response(run)

    async def start_visuals(self, project_id: str, run_id: str) -> RunResponse:
        await self._require_project(project_id)
        run = await StagesService(self._session, self._redis).start_visuals(
            project_id, run_id
        )
        return await self._run_response(run)

    async def skip_visuals(self, project_id: str, run_id: str) -> RunResponse:
        await self._require_project(project_id)
        run = await StagesService(self._session, self._redis).skip_visuals(
            project_id, run_id
        )
        return await self._run_response(run)

    async def get_run_audio_file_path(self, project_id: str, run_id: str) -> Path:
        await self._require_project(project_id)
        run = await self._runs.get(run_id)
        if not run or run.project_id != project_id or not run.audio_s3_key:
            raise AppError(code="NOT_FOUND", message="Audio not found", http_status_code=404)
        try:
            return get_artifact_storage().ensure_local(run.audio_s3_key)
        except FileNotFoundError as exc:
            raise AppError(
                code="NOT_FOUND", message="Audio file missing", http_status_code=404
            ) from exc

    async def get_run_cover_file_path(self, project_id: str, run_id: str) -> Path:
        await self._require_project(project_id)
        run = await self._runs.get(run_id)
        if not run or run.project_id != project_id or not run.cover_s3_key:
            raise AppError(code="NOT_FOUND", message="Cover not found", http_status_code=404)
        try:
            return get_artifact_storage().ensure_local(run.cover_s3_key)
        except FileNotFoundError as exc:
            raise AppError(
                code="NOT_FOUND", message="Cover file missing", http_status_code=404
            ) from exc

    async def _run_response(self, run: ProjectRun) -> RunResponse:
        # After flush/onupdate, updated_at can be expired — refresh before sync validate.
        try:
            await self._session.refresh(run)
        except Exception:
            logger.exception("run_response_refresh_failed run_id=%s", getattr(run, "id", None))
        base = RunResponse.model_validate(run)
        draft = await self._scripts.get_for_run(run.id)
        screenplay = ""
        package: dict | None = None
        # Show screenplay once script stage has produced artifacts
        statuses = ensure_stage_statuses(run)
        # Legacy runs (pre-stages): treat succeeded scripts as awaiting approval
        if (
            run.status == "succeeded"
            and not run.current_stage
            and not (isinstance(run.stage_statuses, dict) and run.stage_statuses)
        ):
            statuses = {
                **default_stage_statuses(),
                "script": "pending_approval",
            }
        script_ready = statuses.get("script") in (
            "pending_approval",
            "approved",
            "generating",
        ) or run.status == "succeeded"
        if script_ready or run.status in ("succeeded", "running", "queued"):
            if draft:
                screenplay = read_screenplay_artifact(draft.screenplay_path)
                package = draft.package_json if isinstance(draft.package_json, dict) else None
            if not screenplay:
                screenplay = read_run_screenplay(run.project_id, run.id)
            if not package:
                loaded = read_run_package(run.project_id, run.id)
                package = loaded if loaded else None
        preview = screenplay[:1200] if screenplay else None
        stages = StagesService(self._session, self._redis)
        artifacts = stages.artifacts_payload(run)
        progress = stages.progress_payload(run)
        return base.model_copy(
            update={
                "screenplay_md": screenplay or None,
                "screenplay_preview": preview,
                "package": package,
                "draft_script_id": draft.id if draft else None,
                "is_draft": draft is not None,
                "part_count": run.part_count,
                "total_duration_sec": run.total_duration_sec,
                "current_stage": run.current_stage
                or ("script" if statuses.get("script") == "pending_approval" else "script"),
                "stage_statuses": statuses,
                "artifacts": RunArtifactsResponse(**artifacts),
                "progress": RunProgressResponse(**progress) if progress else None,
                "revision_notes": run.revision_notes,
            }
        )

    async def _require_project(self, project_id: str):
        row = await self._projects.get(project_id)
        if not row:
            raise AppError(code="NOT_FOUND", message="Project not found", http_status_code=404)
        return row
