from pydantic import BaseModel


class Episode(BaseModel):
    id: str
    series_id: str
    title: str
    language: str
    genre: str
    script: str