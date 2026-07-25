from __future__ import annotations

import json
import logging
import re

from app.integrations.llm.client import chat_completion

logger = logging.getLogger(__name__)

_SYSTEM = """\
You are a story analyst specialising in audio drama for mobile audiences.
Given a screenplay excerpt, identify what makes it emotionally compelling and suggest similar story concepts.

Return ONLY valid JSON with no markdown, no explanation, no extra text:
{
  "why_it_works": ["3 to 5 specific emotional hooks, each 8–15 words"],
  "concepts": [
    {
      "title": "Story Title (2-5 words)",
      "tagline": "One-line pitch, max 12 words",
      "emotional_hook": "Core emotion or tension this concept taps into, max 10 words"
    }
  ]
}
Produce exactly 3-5 why_it_works points and exactly 3 concept suggestions."""

_STUB_RESPONSE = {
    "why_it_works": [
        "High-stakes emotional decision made under time pressure",
        "Protagonist torn between loyalty and personal survival",
        "Revelations reframe the audience's understanding of earlier scenes",
    ],
    "concepts": [
        {
            "title": "The Last Signal",
            "tagline": "A dying detective's final case reopens old wounds",
            "emotional_hook": "Grief disguised as duty",
        },
        {
            "title": "Borrowed Time",
            "tagline": "Two strangers share a secret that could ruin both",
            "emotional_hook": "Complicity born from desperation",
        },
        {
            "title": "After the Rain",
            "tagline": "Rebuilding a life when the person you were is gone",
            "emotional_hook": "Identity loss after trauma",
        },
    ],
}


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        raw = match.group(1)
    return json.loads(raw)


async def analyze_story(screenplay_md: str) -> dict:
    excerpt = screenplay_md[:3500]
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Screenplay:\n\n{excerpt}"},
    ]
    try:
        raw = await chat_completion(messages=messages, max_tokens=1500, temperature=0.85)
        return _extract_json(raw)
    except RuntimeError:
        logger.warning("LLM_API_KEY not set — returning stub story analysis")
        return _STUB_RESPONSE
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("story_analysis: failed to parse LLM response: %s", exc)
        raise
