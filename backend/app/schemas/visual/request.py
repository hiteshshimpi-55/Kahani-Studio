from pydantic import BaseModel, Field

from app.schemas.visual.track import VisualTrack


class PlanVisualRequest(BaseModel):
    series_id: str
    part: int = Field(default=1, ge=1)
    part_duration_sec: float = Field(..., gt=0, le=600)
    beats: list[dict] = Field(default_factory=list)
    narration_sequence: list[dict] = Field(default_factory=list)
    seq_timings: dict[str, dict[str, float]] = Field(default_factory=dict)
    persist: bool = True


class RenderVisualRequest(BaseModel):
    series_id: str
    part: int = Field(default=1, ge=1)
    max_shots: int | None = Field(default=None, ge=1, le=40)
    async_job: bool = False


class PlanVisualResponse(BaseModel):
    track: VisualTrack


class RenderVisualResponse(BaseModel):
    track: VisualTrack | None = None
    job_id: str | None = None
    queued: bool = False
