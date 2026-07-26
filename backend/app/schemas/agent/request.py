from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StartAgentRenderRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    language: Literal["hi", "en"] = "hi"
    title: str | None = Field(default=None, max_length=200)
    total_duration_sec: int | None = Field(default=90, ge=30, le=180)
