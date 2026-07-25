"""
Content extraction for video and audio generation pipelines.

Takes a user prompt and extracts structured keywords/context
that downstream generators can consume.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
import anthropic


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


class ExtractionResult(BaseModel):
    theme: str = Field(description="Core theme or subject of the content")
    narrative: str = Field(description="Brief one-sentence narrative description")
    emotional_tone: str = Field(description="Primary emotional tone (e.g. melancholic, triumphant, mysterious)")
    setting: str = Field(description="Time and place of the content")
    characters: list[str] = Field(description="Characters or entities present")
    action_keywords: list[str] = Field(description="Key actions or events happening")
    keywords: list[str] = Field(description="Top keywords capturing the full context")
    video: VideoContext
    audio: AudioContext
    content_warnings: list[str] = Field(
        default_factory=list,
        description="Any sensitive themes the generators should be aware of",
    )


SYSTEM_PROMPT = """\
You are an expert content analyst for a multimedia generation platform. \
Given a user's creative prompt, extract rich, structured context that video and audio generation \
models can use to create cohesive content.

Be specific and actionable. Prefer concrete descriptors over vague ones.
"""


def extract_content(user_prompt: str, api_key: Optional[str] = None) -> ExtractionResult:
    """
    Extract structured video and audio context from a user prompt.

    Args:
        user_prompt: The raw creative prompt from the user.
        api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.

    Returns:
        ExtractionResult with video keywords, audio keywords, and overall context.
    """
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    response = client.messages.parse(
        model="claude-opus-5",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Extract content from this prompt for video and audio generation:\n\n"
                    f"{user_prompt}"
                ),
            }
        ],
        output_format=ExtractionResult,
    )

    return response.parsed_output


def format_extraction(result: ExtractionResult) -> str:
    """Return a human-readable summary of the extraction result."""
    lines = [
        f"Theme:          {result.theme}",
        f"Narrative:      {result.narrative}",
        f"Emotional Tone: {result.emotional_tone}",
        f"Setting:        {result.setting}",
        "",
        "Keywords:       " + ", ".join(result.keywords),
        "Characters:     " + (", ".join(result.characters) if result.characters else "none"),
        "Actions:        " + ", ".join(result.action_keywords),
        "",
        "--- VIDEO ---",
        f"Style:          {result.video.style}",
        f"Lighting:       {result.video.lighting}",
        "Scenes:         " + "; ".join(result.video.scenes),
        "Objects:        " + ", ".join(result.video.objects),
        "Colors:         " + ", ".join(result.video.colors),
        "Camera:         " + ", ".join(result.video.camera_motion),
        "",
        "--- AUDIO ---",
        f"Genre:          {result.audio.genre}",
        f"Tempo:          {result.audio.tempo}",
        f"Mood:           {result.audio.mood}",
        "Instruments:    " + ", ".join(result.audio.instruments),
        "SFX:            " + (", ".join(result.audio.sound_effects) if result.audio.sound_effects else "none"),
    ]

    if result.content_warnings:
        lines += ["", "Warnings:       " + ", ".join(result.content_warnings)]

    return "\n".join(lines)
