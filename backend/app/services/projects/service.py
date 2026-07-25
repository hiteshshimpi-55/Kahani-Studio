from __future__ import annotations

import json
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
from app.repository.models.project import ChatSession, ProjectAttachment, ProjectRun, Script
from app.repository.projects import (
    AttachmentRepository,
    ChatSessionRepository,
    ProjectRepository,
    RunRepository,
    ScriptRepository,
)
from app.schemas.projects.request import (
    ChatMessageRequest,
    CreateProjectRequest,
    GenerateScriptAudioRequest,
    SaveDraftRequest,
    StartRunRequest,
    UpdateScriptRequest,
)
from app.schemas.projects.response import (
    AttachmentResponse,
    ChatHistoryItem,
    ChatMessageResponse,
    ChatSessionResponse,
    ProjectResponse,
    RunResponse,
    ScriptAudioStatusResponse,
    ScriptDetailResponse,
    ScriptLatestResponse,
    ScriptSummaryResponse,
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
    run_screenplay_path,
    runs_dir,
)
logger = logging.getLogger(__name__)

DEFAULT_NARRATION = {
    "pov": "third_limited",
    "cast_model": "multicast",
    "platform_style": "pocket_fm_serial",
    "soundscape": True,
    "narrators": [{"id": "NARRATOR", "voice_notes": "calm thriller guide"}],
}


class ProjectsService:
    def __init__(self, session: AsyncSession, redis: ArqRedis | None = None) -> None:
        self._session = session
        self._redis = redis
        self._projects = ProjectRepository(session)
        self._attachments = AttachmentRepository(session)
        self._sessions = ChatSessionRepository(session)
        self._runs = RunRepository(session)
        self._scripts = ScriptRepository(session)

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

        run = ProjectRun(
            project_id=project_id,
            session_id=session.id,
            prompt=body.prompt.strip(),
            status="queued",
            narration_config=narration,
            part_count=body.part_count or 4,
            total_duration_sec=body.total_duration_sec or 600,
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
        run_screenplay_path(project_id, run_id).write_text(screenplay, encoding="utf-8")

        out_dir = runs_dir(project_id, run_id)
        version = await self._scripts.next_version(project_id)
        screenplay_path = out_dir / f"screenplay.v{version}.md"
        package_path = out_dir / f"script.v{version}.json"
        screenplay_path.write_text(screenplay, encoding="utf-8")
        package_path.write_text(
            json.dumps(package, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        script = Script(
            project_id=project_id,
            run_id=run_id,
            version=version,
            package_json=package,
            screenplay_path=str(screenplay_path),
            storage_dir=str(out_dir),
        )
        script = await self._scripts.create(script)
        return ScriptDetailResponse(**(await self._script_detail(script)).model_dump())

    async def update_script(
        self, project_id: str, script_id: str, body: UpdateScriptRequest
    ) -> ScriptDetailResponse:
        await self._require_project(project_id)
        script = await self._scripts.get(script_id)
        if not script or script.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Script not found", http_status_code=404)

        path = Path(script.screenplay_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body.screenplay_md, encoding="utf-8")

        # Keep run working copy in sync when present
        run_copy = run_screenplay_path(project_id, script.run_id)
        run_copy.write_text(body.screenplay_md, encoding="utf-8")

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
            if audio_file_path(script.storage_dir).is_file():
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
        path = audio_file_path(script.storage_dir)
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

        # Ready to generate — start run with clarified brief
        brief = str(analysis.get("generation_brief") or message).strip()
        part_count = analysis.get("suggested_part_count") or 4
        run_body = StartRunRequest(
            prompt=brief,
            session_id=session.id,
            part_count=int(part_count) if part_count else 4,
        )
        run = await self.start_run(project_id, run_body)
        content = reply or (
            "Starting discovery and the Script Writer now. You can stop anytime. "
            "When it finishes, review the script and save it as a draft if you like it."
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
        out: list[ScriptSummaryResponse] = []
        for script in rows:
            run = await self._runs.get(script.run_id)
            package = script.package_json or {}
            title = package.get("title") if isinstance(package, dict) else None
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
                    title=title if isinstance(title, str) else None,
                    prompt_snippet=snippet or None,
                    created_at=script.created_at,
                )
            )
        return out

    async def get_script(self, project_id: str, script_id: str) -> ScriptDetailResponse:
        await self._require_project(project_id)
        script = await self._scripts.get(script_id)
        if not script or script.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Script not found", http_status_code=404)
        detail = await self._script_detail(script)
        return ScriptDetailResponse(**detail.model_dump())

    async def _script_detail(self, script) -> ScriptLatestResponse:
        screenplay = ""
        path = Path(script.screenplay_path)
        if path.exists():
            screenplay = path.read_text(encoding="utf-8")
        return ScriptLatestResponse(
            id=script.id,
            project_id=script.project_id,
            run_id=script.run_id,
            version=script.version,
            package=script.package_json,
            screenplay_md=screenplay,
            created_at=script.created_at,
        )

    async def _run_response(self, run: ProjectRun) -> RunResponse:
        base = RunResponse.model_validate(run)
        draft = await self._scripts.get_for_run(run.id)
        screenplay = ""
        if run.status == "succeeded":
            if draft:
                path = Path(draft.screenplay_path)
                if path.exists():
                    screenplay = path.read_text(encoding="utf-8")
            if not screenplay:
                screenplay = read_run_screenplay(run.project_id, run.id)
        preview = screenplay[:1200] if screenplay else None
        return base.model_copy(
            update={
                "screenplay_md": screenplay or None,
                "screenplay_preview": preview,
                "draft_script_id": draft.id if draft else None,
                "is_draft": draft is not None,
            }
        )

    async def _require_project(self, project_id: str):
        row = await self._projects.get(project_id)
        if not row:
            raise AppError(code="NOT_FOUND", message="Project not found", http_status_code=404)
        return row
