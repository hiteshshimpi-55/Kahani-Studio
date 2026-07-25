from datetime import datetime

from pydantic import BaseModel


class RewriteArtifact(BaseModel):
    id: str
    episode_id: str
    version: int
    rewritten_script: str
    created_at: datetime