from __future__ import annotations

from typing import Any, TypedDict


class ProjectGraphState(TypedDict, total=False):
    project_id: str
    run_id: str
    prompt: str
    narration_config: dict[str, Any]
    part_count: int
    total_duration_sec: int
    retrieved_chunks: list[dict[str, Any]]
    source_md: str
    script_package: dict[str, Any] | None
    screenplay_md: str | None
    errors: list[str]
