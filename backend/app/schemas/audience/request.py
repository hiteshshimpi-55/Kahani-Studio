"""Request schemas for audience simulation endpoints."""

from pydantic import BaseModel, Field


class SimulateRequest(BaseModel):
    """Kick off an audience simulation for an episode."""

    episode_id: str = Field(..., min_length=1, description="Episode identifier")
    series_id: str = Field(..., min_length=1, description="Series identifier")
    script: str = Field(..., min_length=10, description="Full script text to simulate against")
    language: str = Field(default="hindi", description="Primary language: hindi | english")
    genre: str = Field(default="thriller", description="Genre tag for persona weighting")
    title: str = Field(default="", description="Episode title (optional)")
    part_count: int = Field(default=5, ge=1, le=20, description="Number of parts in serial")
