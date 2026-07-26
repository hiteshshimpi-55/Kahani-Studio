from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    filename: str
    content_type: str
    size_bytes: int
    index_status: str
    created_at: datetime


class RunArtifactsResponse(BaseModel):
    screenplay_key: str | None = None
    package_key: str | None = None
    audio_key: str | None = None
    cover_key: str | None = None
    manifest_key: str | None = None
    audio_url: str | None = None
    cover_url: str | None = None
    visuals_series_id: str | None = None
    visuals_url: str | None = None


class RunProgressResponse(BaseModel):
    total_lines: int | None = None
    lines_rendered: int | None = None
    duration_sec: float | None = None
    current_step: str | None = None


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    prompt: str
    status: str
    error: str | None
    arq_job_id: str | None
    created_at: datetime
    updated_at: datetime
    session_id: str | None = None
    part_count: int | None = None
    total_duration_sec: int | None = None
    screenplay_preview: str | None = None
    screenplay_md: str | None = None
    package: dict | None = None
    draft_script_id: str | None = None
    is_draft: bool = False
    cast_updated: bool = False
    current_stage: str | None = None
    stage_statuses: dict[str, str] | None = None
    artifacts: RunArtifactsResponse | None = None
    progress: RunProgressResponse | None = None
    revision_notes: str | None = None


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    run_count: int = 0


class ScriptLatestResponse(BaseModel):
    id: str
    project_id: str
    run_id: str
    version: int
    package: dict
    screenplay_md: str
    created_at: datetime
    part_number: int | None = None
    pinned: bool = False
    cliff_out: str | None = None
    title: str | None = None


class ScriptSummaryResponse(BaseModel):
    id: str
    project_id: str
    run_id: str
    version: int
    title: str | None
    prompt_snippet: str | None
    created_at: datetime
    part_number: int | None = None
    pinned: bool = False
    cliff_out: str | None = None
    is_latest_continuity: bool = False


class ScriptDetailResponse(ScriptLatestResponse):
    pass


class CharacterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    character_key: str
    name: str
    role: str | None = None
    voice: str | None = None
    speech_patterns: str | None = None
    arc: str | None = None
    created_at: datetime
    updated_at: datetime


class StoryContextSummaryResponse(BaseModel):
    cast_count: int
    docs_count: int
    episode_count: int
    latest_part_number: int | None = None


class ScriptAudioStatusResponse(BaseModel):
    script_id: str
    project_id: str
    status: str  # idle | queued | running | succeeded | failed
    error: str | None = None
    audio_url: str | None = None
    voice_provider: str | None = None
    line_count: int | None = None
    sfx_clip_count: int | None = None
    title: str | None = None
    updated_at: str | None = None


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    kind: str
    created_at: datetime
    run_id: str | None = None
    questions: list[str] = []
    session_id: str | None = None
    run: RunResponse | None = None


class PlotPitchItem(BaseModel):
    title: str
    logline: str
    tone: str = ""


class ChatHistoryItem(BaseModel):
    id: str
    role: str
    content: str
    kind: str
    created_at: datetime
    run_id: str | None = None
    questions: list[str] = []
    plot_pitches: list[PlotPitchItem] = []
    script_preview: str | None = None
    script_package: dict | None = None
    draft_script_id: str | None = None
    is_draft: bool = False
    run_status: str | None = None


class ExportScriptResponse(BaseModel):
    url: str
    filename: str
    expires_in: int | None = None
