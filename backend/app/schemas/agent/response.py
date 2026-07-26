from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AgentRenderStatus = Literal["queued", "script", "audio", "done", "failed"]


class AgentRenderStartResponse(BaseModel):
    job_id: str
    status: AgentRenderStatus = "queued"
    project_id: str
    run_id: str


class AgentRenderResponse(BaseModel):
    job_id: str
    status: AgentRenderStatus
    phase: str
    project_id: str
    run_id: str
    error: str | None = None
    audio_url: str | None = None
    duration_s: float | None = None
    title: str | None = None
    language: str | None = None
    cliffhanger: str | None = None
    script_excerpt: str | None = None


class McpToolCatalogItem(BaseModel):
    name: str
    description: str
    arguments: list[dict[str, Any]] = Field(default_factory=list)


class McpToolsCatalogResponse(BaseModel):
    mcp_url: str
    tools: list[McpToolCatalogItem]
