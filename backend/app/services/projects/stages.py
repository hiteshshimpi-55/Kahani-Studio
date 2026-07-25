"""Staged production pipeline — script → audio → cover → assembly with human gates."""

from __future__ import annotations

import json
import logging
from typing import Any

from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import AppError
from app.integrations.s3 import get_artifact_storage
from app.repository.models.project import ProjectRun
from app.repository.projects import RunRepository
from app.services.projects.storage import (
    read_run_package,
    read_run_screenplay,
    run_object_prefix,
    write_run_package,
    write_run_screenplay,
)

logger = logging.getLogger(__name__)

STAGES = ("script", "audio", "cover_art", "assembly")
# Optional companion path after audio (lookbook → scene stills → video)
OPTIONAL_STAGES = ("visuals",)
STAGE_STATUS = ("idle", "generating", "pending_approval", "approved", "rejected", "failed")

DEFAULT_STAGE_STATUSES: dict[str, str] = {
    "script": "idle",
    "audio": "idle",
    "visuals": "idle",
    "cover_art": "idle",
    "assembly": "idle",
}

NEXT_STAGE = {
    "script": "audio",
    "audio": "cover_art",
    "cover_art": "assembly",
    "assembly": "complete",
}


def default_stage_statuses() -> dict[str, str]:
    return dict(DEFAULT_STAGE_STATUSES)


def ensure_stage_statuses(run: ProjectRun) -> dict[str, str]:
    raw = run.stage_statuses if isinstance(run.stage_statuses, dict) else {}
    statuses = default_stage_statuses()
    for key in (*STAGES, *OPTIONAL_STAGES):
        if key in raw and isinstance(raw[key], str):
            statuses[key] = raw[key]
    return statuses


def visuals_series_id(run_id: str) -> str:
    """series_id for Pratham visuals pipeline — one episode run → one visual series."""
    return run_id


def run_audio_key(project_id: str, run_id: str) -> str:
    return f"{run_object_prefix(project_id, run_id)}/episode.mp3"


def run_audio_result_key(project_id: str, run_id: str) -> str:
    return f"{run_object_prefix(project_id, run_id)}/audio_result.json"


def run_cover_key(project_id: str, run_id: str) -> str:
    return f"{run_object_prefix(project_id, run_id)}/cover.png"


def run_manifest_key(project_id: str, run_id: str) -> str:
    return f"{run_object_prefix(project_id, run_id)}/manifest.json"


def build_cover_prompt(
    package: dict[str, Any],
    *,
    audio_result: dict[str, Any] | None = None,
    revision_notes: str | None = None,
) -> str:
    title = str(package.get("title") or "Untitled Episode")
    bible = package.get("bible") if isinstance(package.get("bible"), dict) else {}
    chars = bible.get("characters") if isinstance(bible.get("characters"), list) else []
    protagonist = ""
    if chars and isinstance(chars[0], dict):
        name = chars[0].get("name") or chars[0].get("id") or "protagonist"
        role = chars[0].get("role") or ""
        voice = chars[0].get("voice") or ""
        protagonist = f"{name}"
        if role:
            protagonist += f" ({role})"
        if voice:
            protagonist += f", look/vibe: {voice}"

    parts = package.get("parts") if isinstance(package.get("parts"), list) else []
    part_title = ""
    cliff = ""
    if parts and isinstance(parts[0], dict):
        part_title = str(parts[0].get("title") or "")
        cliff = str(parts[0].get("cliff_out") or "")

    mood = "dramatic suspense"
    if audio_result:
        duration = audio_result.get("duration_sec")
        if duration:
            mood = f"cinematic tension over ~{int(float(duration))}s episode"

    prompt = (
        f"Cinematic 9:16 vertical cover art for an audio drama episode titled \"{title}\". "
        f"{'Episode subtitle: ' + part_title + '. ' if part_title else ''}"
        f"Feature {protagonist or 'the lead character'} in a Pocket FM serial style. "
        f"Mood: {mood}. Dramatic lighting, high contrast, no text overlays, no watermarks. "
        f"{'Cliffhanger energy: ' + cliff + '. ' if cliff else ''}"
    )
    if revision_notes and revision_notes.strip():
        prompt += f" User revision notes: {revision_notes.strip()}"
    return prompt.strip()


class StagesService:
    def __init__(self, session: AsyncSession, redis: ArqRedis | None) -> None:
        self._session = session
        self._redis = redis
        self._runs = RunRepository(session)

    async def _get_run(self, project_id: str, run_id: str) -> ProjectRun:
        run = await self._runs.get(run_id)
        if not run or run.project_id != project_id:
            raise AppError(code="NOT_FOUND", message="Run not found", http_status_code=404)
        return run

    async def _save_stages(
        self,
        run: ProjectRun,
        *,
        current_stage: str | None = None,
        stage_statuses: dict[str, str] | None = None,
        audio_s3_key: str | None = None,
        cover_s3_key: str | None = None,
        manifest_s3_key: str | None = None,
        revision_notes: str | None = ...,  # type: ignore[assignment]
        status: str | None = None,
        error: str | None = ...,  # type: ignore[assignment]
        clear_audio: bool = False,
        clear_cover: bool = False,
    ) -> ProjectRun:
        if current_stage is not None:
            run.current_stage = current_stage
        if stage_statuses is not None:
            run.stage_statuses = stage_statuses
        if audio_s3_key is not None:
            run.audio_s3_key = audio_s3_key
        if cover_s3_key is not None:
            run.cover_s3_key = cover_s3_key
        if manifest_s3_key is not None:
            run.manifest_s3_key = manifest_s3_key
        if clear_audio:
            run.audio_s3_key = None
        if clear_cover:
            run.cover_s3_key = None
        if revision_notes is not ...:
            run.revision_notes = revision_notes
        if status is not None:
            run.status = status
        if error is not ...:
            run.error = error
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def mark_script_pending(self, run: ProjectRun) -> ProjectRun:
        statuses = ensure_stage_statuses(run)
        statuses["script"] = "pending_approval"
        for key in ("audio", "cover_art", "assembly"):
            if statuses.get(key) not in ("approved",):
                statuses[key] = "idle"
        return await self._save_stages(
            run,
            current_stage="script",
            stage_statuses=statuses,
            status="succeeded",
            error=None,
        )

    def _hydrate_legacy_statuses(self, run: ProjectRun) -> dict[str, str]:
        statuses = ensure_stage_statuses(run)
        if (
            run.status == "succeeded"
            and not run.current_stage
            and not (isinstance(run.stage_statuses, dict) and run.stage_statuses)
        ):
            # Pre-pipeline runs: script artifact exists, await first approval
            statuses = {**default_stage_statuses(), "script": "pending_approval"}
        return statuses

    async def approve_stage(self, project_id: str, run_id: str, stage: str) -> ProjectRun:
        if stage not in STAGES:
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Unknown stage: {stage}",
                http_status_code=400,
            )
        run = await self._get_run(project_id, run_id)
        statuses = self._hydrate_legacy_statuses(run)

        if statuses.get(stage) == "approved":
            return run
        if statuses.get(stage) != "pending_approval":
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Stage '{stage}' must be pending approval before approving",
                http_status_code=400,
            )

        # Ensure artifacts exist for the stage being approved
        if stage == "script":
            screenplay = read_run_screenplay(project_id, run_id)
            package = read_run_package(project_id, run_id)
            if not screenplay.strip():
                raise AppError(
                    code="VALIDATION_ERROR",
                    message="No screenplay artifact to approve",
                    http_status_code=400,
                )
            # Re-push to S3 to ensure durability on approval
            write_run_screenplay(project_id, run_id, screenplay)
            write_run_package(project_id, run_id, package)

        if stage == "audio" and not run.audio_s3_key:
            raise AppError(
                code="VALIDATION_ERROR",
                message="No audio artifact to approve",
                http_status_code=400,
            )
        if stage == "cover_art" and not run.cover_s3_key:
            raise AppError(
                code="VALIDATION_ERROR",
                message="No cover art to approve",
                http_status_code=400,
            )

        statuses[stage] = "approved"
        next_stage = NEXT_STAGE[stage]
        run = await self._save_stages(
            run,
            current_stage=next_stage if next_stage != "complete" else "complete",
            stage_statuses=statuses,
            revision_notes=None,
            error=None,
        )

        if next_stage == "audio":
            await self._enqueue_audio(run)
        elif next_stage == "cover_art":
            await self._enqueue_cover(run)
        elif next_stage == "assembly":
            await self._enqueue_assembly(run)

        return run

    async def reject_stage(
        self,
        project_id: str,
        run_id: str,
        stage: str,
        *,
        action: str,
        notes: str | None = None,
    ) -> ProjectRun:
        if stage not in STAGES or stage == "assembly":
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Cannot reject stage: {stage}",
                http_status_code=400,
            )
        if action not in ("regenerate", "revise"):
            raise AppError(
                code="VALIDATION_ERROR",
                message="action must be regenerate or revise",
                http_status_code=400,
            )
        if action == "revise" and not (notes or "").strip():
            raise AppError(
                code="VALIDATION_ERROR",
                message="notes are required when action is revise",
                http_status_code=400,
            )

        run = await self._get_run(project_id, run_id)
        statuses = self._hydrate_legacy_statuses(run)
        if statuses.get(stage) not in ("pending_approval", "generating", "failed", "rejected"):
            raise AppError(
                code="VALIDATION_ERROR",
                message=f"Stage '{stage}' cannot be rejected in status '{statuses.get(stage)}'",
                http_status_code=400,
            )

        revision = (notes or "").strip() if action == "revise" else None
        statuses[stage] = "generating"
        # Reset downstream stages
        reset_from = STAGES.index(stage)
        for key in STAGES[reset_from + 1 :]:
            statuses[key] = "idle"

        clear_audio = stage in ("script", "audio")
        clear_cover = stage in ("script", "audio", "cover_art")

        run = await self._save_stages(
            run,
            current_stage=stage,
            stage_statuses=statuses,
            revision_notes=revision,
            clear_audio=clear_audio,
            clear_cover=clear_cover,
            error=None,
            status="running" if stage == "script" else run.status,
        )

        if stage == "script":
            await self._enqueue_script(run, revision_notes=revision)
        elif stage == "audio":
            await self._enqueue_audio(run, revision_notes=revision)
        elif stage == "cover_art":
            await self._enqueue_cover(run, revision_notes=revision)

        return run

    async def _require_redis(self) -> ArqRedis:
        if self._redis is None:
            raise AppError(
                code="INTERNAL_ERROR",
                message="Redis unavailable",
                http_status_code=503,
            )
        return self._redis

    async def _enqueue_script(self, run: ProjectRun, *, revision_notes: str | None = None) -> None:
        redis = await self._require_redis()
        if revision_notes:
            # Append notes into prompt for rewrite pass
            base = run.prompt or ""
            if "Revision notes:" not in base:
                run.prompt = f"{base.rstrip()}\n\nRevision notes: {revision_notes}"
            else:
                run.prompt = f"{base.rstrip()}\n{revision_notes}"
            await self._session.flush()

        statuses = ensure_stage_statuses(run)
        statuses["script"] = "generating"
        await self._save_stages(run, stage_statuses=statuses, status="queued", error=None)

        job = await redis.enqueue_job(
            "project_run_job",
            project_id=run.project_id,
            run_id=run.id,
        )
        job_id = getattr(job, "job_id", None) or str(job)
        await self._runs.update_status(run.id, status="queued", arq_job_id=job_id)
        await self._session.refresh(run)

    async def _enqueue_audio(self, run: ProjectRun, *, revision_notes: str | None = None) -> None:
        redis = await self._require_redis()
        statuses = ensure_stage_statuses(run)
        statuses["audio"] = "generating"
        await self._save_stages(
            run,
            current_stage="audio",
            stage_statuses=statuses,
            revision_notes=revision_notes if revision_notes is not None else run.revision_notes,
            clear_audio=True,
            clear_cover=True,
        )
        job = await redis.enqueue_job(
            "generate_run_audio_job",
            project_id=run.project_id,
            run_id=run.id,
            revision_notes=revision_notes or run.revision_notes,
        )
        job_id = getattr(job, "job_id", None) or str(job)
        run.arq_job_id = job_id
        await self._session.flush()
        await self._session.refresh(run)

    async def _enqueue_cover(self, run: ProjectRun, *, revision_notes: str | None = None) -> None:
        redis = await self._require_redis()
        statuses = ensure_stage_statuses(run)
        statuses["cover_art"] = "generating"
        await self._save_stages(
            run,
            current_stage="cover_art",
            stage_statuses=statuses,
            revision_notes=revision_notes if revision_notes is not None else run.revision_notes,
            clear_cover=True,
        )
        job = await redis.enqueue_job(
            "generate_cover_art_job",
            project_id=run.project_id,
            run_id=run.id,
            revision_notes=revision_notes or run.revision_notes,
        )
        job_id = getattr(job, "job_id", None) or str(job)
        run.arq_job_id = job_id
        await self._session.flush()
        await self._session.refresh(run)

    async def _enqueue_assembly(self, run: ProjectRun) -> None:
        redis = await self._require_redis()
        statuses = ensure_stage_statuses(run)
        statuses["assembly"] = "generating"
        await self._save_stages(
            run,
            current_stage="assembly",
            stage_statuses=statuses,
        )
        job = await redis.enqueue_job(
            "assemble_episode_job",
            project_id=run.project_id,
            run_id=run.id,
        )
        job_id = getattr(job, "job_id", None) or str(job)
        run.arq_job_id = job_id
        await self._session.flush()
        await self._session.refresh(run)

    async def start_visuals(self, project_id: str, run_id: str) -> ProjectRun:
        """After audio exists: queue lookbook + scene stills (optional companion path)."""
        run = await self._get_run(project_id, run_id)
        statuses = self._hydrate_legacy_statuses(run)
        if not run.audio_s3_key:
            raise AppError(
                code="VALIDATION_ERROR",
                message="Generate audio before companion visuals",
                http_status_code=400,
            )
        if statuses.get("visuals") == "generating":
            return run

        statuses["visuals"] = "generating"
        run = await self._save_stages(
            run,
            stage_statuses=statuses,
            error=None,
        )
        redis = await self._require_redis()
        job = await redis.enqueue_job(
            "project_run_visuals_job",
            project_id=run.project_id,
            run_id=run.id,
        )
        job_id = getattr(job, "job_id", None) or str(job)
        run.arq_job_id = job_id
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def skip_visuals(self, project_id: str, run_id: str) -> ProjectRun:
        """User declined companion visuals — continue cover/assembly path."""
        run = await self._get_run(project_id, run_id)
        statuses = self._hydrate_legacy_statuses(run)
        if statuses.get("visuals") == "generating":
            raise AppError(
                code="VALIDATION_ERROR",
                message="Visuals are already generating",
                http_status_code=400,
            )
        statuses["visuals"] = "rejected"
        return await self._save_stages(run, stage_statuses=statuses, error=None)

    def artifacts_payload(self, run: ProjectRun) -> dict[str, str | None]:
        prefix = run_object_prefix(run.project_id, run.id)
        series_id = visuals_series_id(run.id)
        return {
            "screenplay_key": f"{prefix}/screenplay.md",
            "package_key": f"{prefix}/script.json",
            "audio_key": run.audio_s3_key,
            "cover_key": run.cover_s3_key,
            "manifest_key": run.manifest_s3_key,
            "audio_url": (
                f"/api/v1/projects/{run.project_id}/runs/{run.id}/audio/file"
                if run.audio_s3_key
                else None
            ),
            "cover_url": (
                f"/api/v1/projects/{run.project_id}/runs/{run.id}/cover"
                if run.cover_s3_key
                else None
            ),
            "visuals_series_id": series_id,
            "visuals_url": f"/api/v1/visuals/{series_id}",
        }

    def progress_payload(self, run: ProjectRun) -> dict[str, Any] | None:
        """Best-effort progress from audio_result sidecar if present."""
        if not run.audio_s3_key and (run.current_stage or "") != "audio":
            return None
        key = run_audio_result_key(run.project_id, run.id)
        try:
            raw = get_artifact_storage().get_text(key)
            data = json.loads(raw)
            if not isinstance(data, dict):
                return None
            return {
                "total_lines": data.get("line_count") or data.get("total_lines"),
                "lines_rendered": data.get("lines_rendered"),
                "duration_sec": data.get("duration_sec"),
                "current_step": data.get("current_step"),
            }
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None
