from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class StartRunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    narration_config: dict | None = None
    part_count: int | None = Field(default=None, ge=1, le=12)
    total_duration_sec: int | None = Field(default=None, ge=30, le=1200)


class UpdateScriptRequest(BaseModel):
    screenplay_md: str = Field(min_length=1)


class SaveDraftRequest(BaseModel):
    screenplay_md: str | None = None
