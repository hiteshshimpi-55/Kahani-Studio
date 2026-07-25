"""Response schemas for audience simulation endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Patch
# ---------------------------------------------------------------------------


class PatchResponse(BaseModel):
    id: str
    beat_id: str
    part: int
    patch_type: str
    rationale: str
    suggested_text: str | None = None
    expected_delta: dict | None = None
    status: str  # PENDING / ACCEPTED / REJECTED


# ---------------------------------------------------------------------------
# Structural Audit
# ---------------------------------------------------------------------------


class AuditScoreResponse(BaseModel):
    name: str
    score: float
    comment: str


class StructuralAuditResponse(BaseModel):
    overall_score: float
    hook_score: AuditScoreResponse
    pacing_score: AuditScoreResponse
    dialogue_score: AuditScoreResponse
    cliffhanger_score: AuditScoreResponse


# ---------------------------------------------------------------------------
# Engagement Report (per-part funnel)
# ---------------------------------------------------------------------------


class PartFunnelResponse(BaseModel):
    part: int
    start_rate: float
    p_continue: float
    drop_reasons: list[str]
    fragile_beats: list[str]
    cohort_disagreements: list[str]


class EngagementReportResponse(BaseModel):
    persona_count: int
    calibration_status: str
    funnel: list[PartFunnelResponse]


# ---------------------------------------------------------------------------
# Full Sim Run
# ---------------------------------------------------------------------------


class SimRunSummaryResponse(BaseModel):
    id: str
    episode_id: str
    series_id: str
    status: str
    calibration_status: str
    persona_count: int | None = None
    created_at: datetime


class SimRunResponse(BaseModel):
    id: str
    episode_id: str
    series_id: str
    status: str
    calibration_status: str
    persona_count: int | None = None
    created_at: datetime
    audit: StructuralAuditResponse | None = None
    engagement: EngagementReportResponse | None = None
    patches: list[PatchResponse] = []
    error: str | None = None


# ---------------------------------------------------------------------------
# Enqueue response
# ---------------------------------------------------------------------------


class EnqueueSimResponse(BaseModel):
    sim_run_id: str
    queued: bool


# ---------------------------------------------------------------------------
# Patch decision
# ---------------------------------------------------------------------------


class PatchDecisionRequest(BaseModel):
    status: str  # "ACCEPTED" or "REJECTED"
