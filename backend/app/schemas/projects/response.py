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
    screenplay_preview: str | None = None
    screenplay_md: str | None = None
    draft_script_id: str | None = None
    is_draft: bool = False


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


class ScriptSummaryResponse(BaseModel):
    id: str
    project_id: str
    run_id: str
    version: int
    title: str | None
    prompt_snippet: str | None
    created_at: datetime


class ScriptDetailResponse(ScriptLatestResponse):
    pass


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
    draft_script_id: str | None = None
    is_draft: bool = False
    run_status: str | None = None
