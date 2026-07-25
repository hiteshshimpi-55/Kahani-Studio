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


class ScriptLatestResponse(BaseModel):
    id: str
    project_id: str
    run_id: str
    version: int
    package: dict
    screenplay_md: str
    created_at: datetime
