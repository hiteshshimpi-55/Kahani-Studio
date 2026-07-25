from typing import Any

from pydantic import BaseModel


class HealthDependencyStatus(BaseModel):
    ok: bool
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    postgres: HealthDependencyStatus
    redis: HealthDependencyStatus
    data_dir: str


class Envelope(BaseModel):
    data: dict[str, Any]
