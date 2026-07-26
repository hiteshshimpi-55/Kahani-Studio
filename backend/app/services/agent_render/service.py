"""Headless agent render: prompt → project/run → script → auto-approve → audio URL."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.errors import AppError
from app.integrations.s3 import get_artifact_storage, presigned_url, s3_enabled
from app.repository.models.project import ProjectRun
from app.repository.projects import RunRepository
from app.schemas.agent.request import StartAgentRenderRequest
from app.schemas.agent.response import (
    AgentRenderResponse,
    AgentRenderStartResponse,
    AgentRenderStatus,
)
from app.schemas.projects.request import CreateProjectRequest, StartRunRequest
from app.services.projects.service import DEFAULT_NARRATION, ProjectsService
from app.services.projects.stages import ensure_stage_statuses, run_audio_result_key
from app.services.projects.storage import read_run_package, read_run_screenplay

logger = logging.getLogger(__name__)


def is_headless_run(run: ProjectRun) -> bool:
    cfg = run.narration_config if isinstance(run.narration_config, dict) else {}
    return bool(cfg.get("headless"))


def _slug_title(title: str | None, prompt: str) -> str:
    raw = (title or "").strip() or prompt.strip().split("\n", 1)[0][:80]
    cleaned = re.sub(r"\s+", " ", raw).strip() or "Agent episode"
    return cleaned[:120]


class AgentRenderService:
    def __init__(self, session: AsyncSession, redis: ArqRedis | None = None) -> None:
        self._session = session
        self._redis = redis
        self._runs = RunRepository(session)
        self._projects_svc = ProjectsService(session, redis)

    async def start_render(self, body: StartAgentRenderRequest) -> AgentRenderStartResponse:
        title = _slug_title(body.title, body.prompt)
        project = await self._projects_svc.create_project(
            CreateProjectRequest(
                name=f"MCP · {title}"[:120],
                description="Headless agent render (MCP / API)",
            )
        )
        narration = {
            **DEFAULT_NARRATION,
            "headless": True,
            "language": body.language,
            "agent_title": title,
        }
        run = await self._projects_svc.start_run(
            project.id,
            StartRunRequest(
                prompt=body.prompt.strip(),
                narration_config=narration,
                total_duration_sec=body.total_duration_sec or 90,
            ),
        )
        return AgentRenderStartResponse(
            job_id=run.id,
            status="queued",
            project_id=project.id,
            run_id=run.id,
        )

    async def get_render(self, job_id: str) -> AgentRenderResponse:
        run = await self._runs.get(job_id)
        if not run:
            raise AppError(code="NOT_FOUND", message="Render job not found", http_status_code=404)

        status, phase = self._map_status(run)
        title, language = self._title_language(run)
        audio_url = self._audio_url(run) if run.audio_s3_key else None
        duration_s, cliffhanger, excerpt = None, None, None
        if status == "done":
            duration_s, cliffhanger, excerpt = self._done_meta(run)

        return AgentRenderResponse(
            job_id=run.id,
            status=status,
            phase=phase,
            project_id=run.project_id,
            run_id=run.id,
            error=run.error if status == "failed" else None,
            audio_url=audio_url,
            duration_s=duration_s,
            title=title,
            language=language,
            cliffhanger=cliffhanger,
            script_excerpt=excerpt,
        )

    def _map_status(self, run: ProjectRun) -> tuple[AgentRenderStatus, str]:
        if run.status == "failed" or run.status == "cancelled":
            return "failed", run.status
        statuses = ensure_stage_statuses(run)
        if statuses.get("audio") == "failed" or statuses.get("script") == "failed":
            return "failed", "stage_failed"
        if run.audio_s3_key:
            return "done", "audio_ready"
        if statuses.get("audio") == "generating":
            return "audio", "generating_audio"
        if statuses.get("script") in ("pending_approval", "approved"):
            # Headless should auto-advance; brief window or non-headless leftover
            return "audio", "awaiting_audio"
        if statuses.get("script") == "generating" or run.status in ("queued", "running"):
            return "script", "generating_script"
        return "queued", run.status or "queued"

    def _title_language(self, run: ProjectRun) -> tuple[str | None, str | None]:
        cfg = run.narration_config if isinstance(run.narration_config, dict) else {}
        title = cfg.get("agent_title")
        if isinstance(title, str) and title.strip():
            title_out: str | None = title.strip()
        else:
            title_out = None
        lang = cfg.get("language")
        language = lang if lang in ("hi", "en") else None
        return title_out, language

    def _audio_url(self, run: ProjectRun) -> str | None:
        if not run.audio_s3_key:
            return None
        if s3_enabled():
            try:
                return presigned_url(run.audio_s3_key)
            except Exception:
                logger.exception("agent_render_presign_failed")
        base = (settings.public_api_base_url or "").rstrip("/")
        path = f"/api/v1/projects/{run.project_id}/runs/{run.id}/audio/file"
        if base:
            return f"{base}{path}"
        # Relative — MCP clients should prefer PUBLIC_API_BASE_URL set
        return path

    def _done_meta(
        self, run: ProjectRun
    ) -> tuple[float | None, str | None, str | None]:
        duration_s: float | None = None
        cliffhanger: str | None = None
        excerpt: str | None = None

        try:
            raw = get_artifact_storage().get_text(
                run_audio_result_key(run.project_id, run.id)
            )
            payload = json.loads(raw) if raw else {}
            if isinstance(payload, dict):
                dur = payload.get("duration_sec") or payload.get("duration_s")
                if isinstance(dur, (int, float)):
                    duration_s = float(dur)
        except Exception:
            logger.debug("agent_render_audio_meta_missing", exc_info=True)

        if duration_s is None and run.total_duration_sec:
            duration_s = float(run.total_duration_sec)

        try:
            package = read_run_package(run.project_id, run.id)
            cliffhanger = _extract_cliffhanger(package)
        except Exception:
            logger.debug("agent_render_package_missing", exc_info=True)

        try:
            screenplay = read_run_screenplay(run.project_id, run.id)
            excerpt = (screenplay or "").strip()[:600] or None
        except Exception:
            logger.debug("agent_render_screenplay_missing", exc_info=True)

        return duration_s, cliffhanger, excerpt


def _extract_cliffhanger(package: dict[str, Any]) -> str | None:
    for key in ("cliffhanger", "ending_hook", "hook"):
        val = package.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()[:400]
    parts = package.get("parts") or package.get("episodes")
    if isinstance(parts, list) and parts:
        last = parts[-1]
        if isinstance(last, dict):
            for key in ("cliffhanger", "ending", "hook"):
                val = last.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()[:400]
    return None
