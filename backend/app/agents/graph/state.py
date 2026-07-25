from __future__ import annotations

from typing import Any, TypedDict


class ProjectGraphState(TypedDict, total=False):
    project_id: str
    run_id: str
    prompt: str
    narration_config: dict[str, Any]
    part_count: int
    total_duration_sec: int
    part_number: int
    series_cast: list[dict[str, Any]]
    continuity_episodes: list[dict[str, Any]]
    retrieved_chunks: list[dict[str, Any]]
    # Parminal discovery: LLM extraction + Tavily crawl
    discovery_md: str
    extraction: dict[str, Any] | None
    crawl: dict[str, Any] | None
    source_md: str
    script_package: dict[str, Any] | None
    screenplay_md: str | None
    audio_result: dict[str, Any] | None
    audio_s3_key: str | None
    cover_image_url: str | None
    errors: list[str]
