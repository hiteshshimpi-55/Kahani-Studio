from pydantic import BaseModel


class TopicCard(BaseModel):
    id: str
    title: str
    genre: str
    mood: str
    hook: str
    tags: list[str]
    why_trending: str


class TrendingTopicsResponse(BaseModel):
    region: str
    region_name: str
    state: str = ""
    topics: list[TopicCard]
