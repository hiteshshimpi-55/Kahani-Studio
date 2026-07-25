from pydantic import BaseModel, Field


class WebReference(BaseModel):
    url: str
    title: str
    snippet: str
    category: str = Field(
        description="topic_context | similar_work | character_reference | "
                    "visual_reference | audio_reference"
    )


class CharacterResearch(BaseModel):
    name: str
    role: str
    references: list[WebReference]
    summary: str = Field(description="What was found about this character online")


class CrawlResponse(BaseModel):
    topic_context: str = Field(
        description="Background context or real-world information about the topic"
    )
    similar_works: list[WebReference] = Field(
        description="Movies, shows, songs, or stories similar to this content"
    )
    character_research: list[CharacterResearch] = Field(
        default_factory=list,
        description="Web research per character. Empty if prompt had no characters.",
    )
    visual_references: list[WebReference] = Field(
        description="Visual style references, cinematography examples, art direction links"
    )
    audio_references: list[WebReference] = Field(
        description="Music tracks, composers, or audio style references"
    )
    all_sources: list[WebReference] = Field(
        description="Flat list of every source found across all categories"
    )
