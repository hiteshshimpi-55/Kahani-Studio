from enum import Enum
from pydantic import BaseModel


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AudienceJob(BaseModel):
    job_id: str
    episode_id: str
    status: JobStatus