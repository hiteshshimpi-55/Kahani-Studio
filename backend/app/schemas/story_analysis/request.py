from pydantic import BaseModel


class StoryAnalysisRequest(BaseModel):
    screenplay_md: str
