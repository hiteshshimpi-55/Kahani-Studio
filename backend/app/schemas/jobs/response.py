from pydantic import BaseModel


class EnqueuePingResponse(BaseModel):
    job_id: str | None
    queued: bool


class DbPingResponse(BaseModel):
    id: int
    source: str
