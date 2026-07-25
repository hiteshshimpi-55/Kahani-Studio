from pydantic import BaseModel


class ConceptSuggestion(BaseModel):
    title: str
    tagline: str
    emotional_hook: str


class StoryAnalysisResponse(BaseModel):
    why_it_works: list[str]
    concepts: list[ConceptSuggestion]
