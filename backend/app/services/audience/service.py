"""Service layer for audience simulation."""

from __future__ import annotations

from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.audience import audience as audience_repo
from app.repository.models.audience import PatchStatus
from app.schemas.audience.request import SimulateRequest
from app.schemas.audience.response import (
    AuditScoreResponse,
    EnqueueSimResponse,
    EngagementReportResponse,
    PatchResponse,
    PartFunnelResponse,
    SimRunResponse,
    SimRunSummaryResponse,
    StructuralAuditResponse,
)


class AudienceService:
    def __init__(self, redis: ArqRedis, db: AsyncSession) -> None:
        self._redis = redis
        self._db = db

    async def enqueue_simulation(self, req: SimulateRequest) -> EnqueueSimResponse:
        """Create a SimRun record and enqueue the worker job."""
        sim_run = await audience_repo.create_sim_run(
            self._db,
            episode_id=req.episode_id,
            series_id=req.series_id,
        )

        payload = {
            "script": req.script,
            "part_count": req.part_count,
            "genre": req.genre,
            "language": req.language,
            "persona_count": 24,
        }

        await self._redis.enqueue_job("audience_sim_job", sim_run.id, payload)
        return EnqueueSimResponse(sim_run_id=sim_run.id, queued=True)

    async def get_sim_run(self, sim_run_id: str) -> SimRunResponse | None:
        """Get a sim run with full details."""
        run = await audience_repo.get_sim_run(self._db, sim_run_id)
        if not run:
            return None
        return self._to_response(run)

    async def list_sim_runs(self, episode_id: str) -> list[SimRunSummaryResponse]:
        """List all sim runs for an episode."""
        runs = await audience_repo.get_sim_runs_for_episode(self._db, episode_id)
        return [
            SimRunSummaryResponse(
                id=r.id,
                episode_id=r.episode_id,
                series_id=r.series_id,
                status=r.status.value,
                calibration_status=r.calibration_status.value,
                persona_count=r.persona_count,
                created_at=r.created_at,
            )
            for r in runs
        ]

    async def decide_patch(self, patch_id: str, accepted: bool) -> PatchResponse | None:
        """Accept or reject a patch."""
        status = PatchStatus.ACCEPTED if accepted else PatchStatus.REJECTED
        patch = await audience_repo.update_patch_status(self._db, patch_id, status)
        if not patch:
            return None
        return PatchResponse(
            id=patch.id,
            beat_id=patch.beat_id,
            part=patch.part,
            patch_type=patch.patch_type,
            rationale=patch.rationale,
            suggested_text=patch.suggested_text,
            expected_delta=patch.expected_delta,
            status=patch.status.value,
        )

    def _to_response(self, run) -> SimRunResponse:
        """Map DB SimRun → API response."""
        audit = None
        if run.audit_result:
            ar = run.audit_result
            audit = StructuralAuditResponse(
                overall_score=ar["overall_score"],
                hook_score=AuditScoreResponse(**ar["hook_score"]),
                pacing_score=AuditScoreResponse(**ar["pacing_score"]),
                dialogue_score=AuditScoreResponse(**ar["dialogue_score"]),
                cliffhanger_score=AuditScoreResponse(**ar["cliffhanger_score"]),
            )

        engagement = None
        if run.engagement_report:
            er = run.engagement_report
            engagement = EngagementReportResponse(
                persona_count=er["persona_count"],
                calibration_status=er["calibration_status"],
                funnel=[PartFunnelResponse(**f) for f in er.get("funnel", [])],
            )

        patches = [
            PatchResponse(
                id=p.id,
                beat_id=p.beat_id,
                part=p.part,
                patch_type=p.patch_type,
                rationale=p.rationale,
                suggested_text=p.suggested_text,
                expected_delta=p.expected_delta,
                status=p.status.value,
            )
            for p in (run.patches or [])
        ]

        return SimRunResponse(
            id=run.id,
            episode_id=run.episode_id,
            series_id=run.series_id,
            status=run.status.value,
            calibration_status=run.calibration_status.value,
            persona_count=run.persona_count,
            created_at=run.created_at,
            audit=audit,
            engagement=engagement,
            patches=patches,
            error=run.error,
        )
