from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, Field


class Character(BaseModel):
    name: str = Field(description="Character name or identifier")
    description: str = Field(description="Physical and personality description")
    role: str = Field(description="Role in the story: protagonist, antagonist, supporting, narrator")
    traits: list[str] = Field(description="Key personality or visual traits")
    backstory: Optional[str] = Field(default=None, description="Brief backstory or motivation if inferable")


class CharacterRelationship(BaseModel):
    from_character: str = Field(description="Name of the first character")
    to_character: str = Field(description="Name of the second character")
    relationship: str = Field(description="Nature of the relationship (e.g. rivals, allies, parent-child, lovers)")
    dynamic: str = Field(description="How they interact or affect each other in the story")


class PlotPoint(BaseModel):
    order: int = Field(description="Sequence position, starting from 1")
    description: str = Field(description="What happens at this point in the story")


class Plot(BaseModel):
    summary: str = Field(description="One-paragraph overview of the full plot")
    points: list[PlotPoint] = Field(description="Ordered list of key story beats")
    conflict: Optional[str] = Field(default=None, description="Central conflict or tension driving the story")
    resolution: Optional[str] = Field(default=None, description="How the story resolves, if present")


class VideoContext(BaseModel):
    scenes: list[str] = Field(description="Visual scenes or settings to depict")
    objects: list[str] = Field(description="Key objects or props")
    colors: list[str] = Field(description="Dominant color palette or mood colors")
    style: str = Field(description="Cinematic/visual style (e.g. cinematic, animated, documentary)")
    lighting: str = Field(description="Lighting mood (e.g. golden hour, dark, neon)")
    camera_motion: list[str] = Field(description="Suggested camera movements (e.g. slow pan, close-up)")


class AudioContext(BaseModel):
    genre: str = Field(description="Music genre (e.g. orchestral, electronic, acoustic)")
    tempo: str = Field(description="Tempo/pace (e.g. slow, moderate, fast, 120 BPM)")
    instruments: list[str] = Field(description="Suggested instruments or sound elements")
    mood: str = Field(description="Emotional tone for the audio")
    sound_effects: list[str] = Field(description="Non-music sound effects to include")


class ExtractionResponse(BaseModel):
    topic: str = Field(description="The core topic or subject of the video/audio content")
    theme: str = Field(description="Underlying thematic message or idea")
    narrative: str = Field(description="Brief one-sentence narrative description")
    emotional_tone: str = Field(description="Primary emotional tone (e.g. melancholic, triumphant, mysterious)")
    setting: str = Field(description="Time and place of the content")
    characters: list[Character] = Field(
        default_factory=list,
        description="Characters present in the content. Empty if the prompt has no characters.",
    )
    relationships: list[CharacterRelationship] = Field(
        default_factory=list,
        description="Relationships between characters. Empty if fewer than two characters.",
    )
    plot: Optional[Plot] = Field(
        default=None,
        description="Structured plot. None if the prompt is non-narrative.",
    )
    action_keywords: list[str] = Field(description="Key actions or events happening")
    keywords: list[str] = Field(description="Top keywords capturing the full context")
    video: VideoContext
    audio: AudioContext
    content_warnings: list[str] = Field(default_factory=list)
    source: str = Field(default="openai:gpt-4o", description="Model that generated this extraction")
