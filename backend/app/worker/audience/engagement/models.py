"""Domain models for engagement simulation results."""

from pydantic import BaseModel, Field


class PartFunnel(BaseModel):
    """Aggregated engagement metrics for a single part."""

    part: int
    start_rate: float = Field(ge=0, le=1, description="% of cohort that starts this part")
    p_continue: float = Field(ge=0, le=1, description="P(continues to next part)")
    drop_reasons: list[str] = Field(default_factory=list)
    fragile_beats: list[str] = Field(default_factory=list, description="beat_ids at highest drop risk")
    cohort_disagreements: list[str] = Field(
        default_factory=list,
        description="Cohort segments that diverge from consensus on this part",
    )


class EngagementReport(BaseModel):
    """Full engagement report aggregated across all personas and parts."""

    persona_count: int
    calibration_status: str = "UNCALIBRATED"
    funnel: list[PartFunnel] = Field(default_factory=list)
