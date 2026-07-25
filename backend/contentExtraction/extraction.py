"""
Content extraction for video and audio generation pipelines.

Takes a user prompt and extracts structured keywords/context
that downstream generators can consume.

Uses OpenAI with structured outputs (beta.chat.completions.parse).
"""

import logging

from openai import OpenAI

from app.core.config import settings

log = logging.getLogger(__name__)
from app.schemas.extraction.response import ExtractionResponse


SYSTEM_PROMPT = """\
You are an expert content analyst for a multimedia generation platform.
Given a user's creative prompt, extract rich, structured context that video and audio generation
models can use to create cohesive content.

Rules:
- Always extract topic, theme, narrative, emotional_tone, setting, keywords, action_keywords, video, and audio.
- Extract characters only if the prompt explicitly mentions or implies named/described people, creatures, or entities.
  If there are no characters, return an empty list.
- For each character, infer backstory and motivation if enough context exists; otherwise leave backstory null.
- Extract relationships between characters if two or more characters exist. Describe the nature and dynamic of each pair.
- Extract plot only if the prompt describes a sequence of events or a story arc.
  If it is a mood piece or abstract prompt with no narrative, return null for plot.
- Be specific and actionable. Prefer concrete descriptors over vague ones.
"""


def _get_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def extract_content(user_prompt: str) -> ExtractionResponse:
    """
    Extract structured video and audio context from a user prompt.

    Args:
        user_prompt: The raw creative prompt from the user.

    Returns:
        ExtractionResponse with topic, characters, plot, video/audio keywords, and overall context.
    """
    client = _get_client()
    log.info("openai_extract_start model=%r", settings.openai_model)

    completion = client.beta.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Extract content from this prompt for video and audio generation:\n\n"
                    f"{user_prompt}"
                ),
            },
        ],
        response_format=ExtractionResponse,
    )

    parsed = completion.choices[0].message.parsed
    log.info(
        "openai_extract_done topic=%r finish_reason=%r",
        parsed.topic,
        completion.choices[0].finish_reason,
    )
    return parsed


def format_extraction(result: ExtractionResponse) -> str:
    """Return a human-readable summary of the extraction result."""
    lines = [
        f"Topic:          {result.topic}",
        f"Theme:          {result.theme}",
        f"Narrative:      {result.narrative}",
        f"Emotional Tone: {result.emotional_tone}",
        f"Setting:        {result.setting}",
        "",
        "Keywords:       " + ", ".join(result.keywords),
        "Actions:        " + ", ".join(result.action_keywords),
    ]

    if result.characters:
        lines += ["", "--- CHARACTERS ---"]
        for c in result.characters:
            lines.append(f"  {c.name} ({c.role}): {c.description}")
            if c.traits:
                lines.append(f"    Traits: {', '.join(c.traits)}")

    if result.plot:
        lines += ["", "--- PLOT ---", f"  {result.plot.summary}"]
        if result.plot.conflict:
            lines.append(f"  Conflict: {result.plot.conflict}")
        if result.plot.resolution:
            lines.append(f"  Resolution: {result.plot.resolution}")
        for pt in result.plot.points:
            lines.append(f"  {pt.order}. {pt.description}")

    lines += [
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
