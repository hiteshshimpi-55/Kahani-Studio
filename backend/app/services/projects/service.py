from __future__ import annotations

import json
import logging
from pathlib import Path

from arq.connections import ArqRedis
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import AppError
from app.repository.models.project import ProjectAttachment, ProjectRun, Script
from app.repository.projects import (
    AttachmentRepository,
    ProjectRepository,
    RunRepository,
    ScriptRepository,
)
from app.schemas.projects.request import (
    CreateProjectRequest,
    SaveDraftRequest,
    StartRunRequest,
    UpdateScriptRequest,
)
from app.schemas.projects.response import (
    AttachmentResponse,
    ProjectResponse,
    RunResponse,
    ScriptDetailResponse,
    ScriptLatestResponse,
    ScriptSummaryResponse,
)
from app.services.projects.storage import (
    attachment_storage_path,
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
        path = attachment_storage_path(project_id, attachment.id, filename)
        path.write_bytes(data)
        attachment.storage_path = str(path)
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

        path = Path(row.storage_path)
        if self._redis is not None:
            try:
                await self._redis.enqueue_job(
                    "delete_attachment_index_job",
                    project_id=project_id,
                    attachment_id=attachment_id,
                )
            except Exception:
                logger.exception("Failed to enqueue delete_attachment_index_job")

        if path.exists():
            path.unlink()
        await self._attachments.delete(row)

    async def start_run(self, project_id: str, body: StartRunRequest) -> RunResponse:
        await self._require_project(project_id)
        narration = body.narration_config or DEFAULT_NARRATION
        run = ProjectRun(
            project_id=project_id,
            prompt=body.prompt.strip(),
            status="queued",
            narration_config=narration,
            part_count=body.part_count or 4,
            total_duration_sec=body.total_duration_sec or 600,
        )
        run = await self._runs.create(run)

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

    async def list_runs(self, project_id: str) -> list[RunResponse]:
        await self._require_project(project_id)
        rows = await self._runs.list_for_project(project_id)
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
