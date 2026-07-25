from typing import Any

from pydantic import BaseModel, Field


class TimelineItem(BaseModel):
    shot_id: str
    t_start_sec: float
    t_end_sec: float
    media_kind: str
    asset_url: str | None = None
    visual_intent: str | None = None
    trigger_reason: str | None = None
    view: dict[str, Any] | None = None


class TimelineResponse(BaseModel):
    series_id: str
    part: int
    aspect_ratio: str
    density: str
    items: list[TimelineItem] = Field(default_factory=list)
