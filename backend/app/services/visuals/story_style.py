"""Story style layer — derive the visual identity from the script itself.

Every downstream prompt (director, lookbook, stills) starts from this
guide, so a cricket story renders bright daylight stadiums and a crime
thriller renders noir — nothing defaults to dark/moody anymore.

Primary path: one Gemini JSON call analysing the script.
Fallback: keyword genre detection with sane per-genre presets.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

log = logging.getLogger(__name__)

# Ordered — first match wins in the heuristic fallback.
_GENRE_KEYWORDS: list[tuple[str, str]] = [
    ("sports", r"cricket|football|kabaddi|match|stadium|tournament|खेल|क्रिकेट|मैदान|टीम|जीत"),
    ("horror", r"ghost|haunt|paranormal|भूत|आत्मा|डरावन|प्रेत|साया"),
    ("crime_thriller", r"murder|crime|police|inspector|forensic|detective|खून|हत्या|पुलिस|लाश|जासूस|अपराध"),
    ("romance", r"love|romance|प्यार|इश्क़|मोहब्बत|दिल|शादी|wedding"),
    ("comedy", r"comedy|funny|hilarious|मज़ाक|हंसी|कॉमेडी"),
    ("mythology", r"mytholog|पुराण|देवता|ऋषि|राक्षस|महल|राजा|kingdom|राज्य"),
    ("family_drama", r"family|परिवार|माँ|पिताजी|बेटा|बेटी|बहू|सास|घर"),
]

_GENRE_PRESETS: dict[str, dict[str, str]] = {
    "sports": {
        "film_look": "vibrant sports-drama cinematography, crisp and energetic",
        "palette": "bright greens, sky blues, warm sunlight, team colors",
        "lighting": "bright natural daylight, open sun, high visibility",
        "default_time_of_day": "day",
        "environment_notes": "open stadiums, practice grounds, dressing rooms — lively and sunlit",
        "expression_notes": "determination, joy, tension of the game, celebration",
    },
    "horror": {
        "film_look": "atmospheric horror, deep shadows, unsettling stillness",
        "palette": "desaturated cold tones, sickly greens, deep blacks",
        "lighting": "low-key, moonlight and flickering practicals",
        "default_time_of_day": "night",
        "environment_notes": "isolated houses, corridors, fog — dread in every frame",
        "expression_notes": "fear, dread, wide eyes, held breath",
    },
    "crime_thriller": {
        "film_look": "gritty neo-noir thriller, high contrast",
        "palette": "deep blues, cool grays, sodium-lamp ambers",
        "lighting": "low-key at night, bright and clinical in labs/offices",
        "default_time_of_day": "night",
        "environment_notes": "police stations, city streets, forensic labs — grounded realism",
        "expression_notes": "suspicion, resolve, grief, quiet menace",
    },
    "romance": {
        "film_look": "soft romantic cinematography, gentle bloom",
        "palette": "warm golds, blush pinks, soft pastels",
        "lighting": "golden hour, warm practicals, flattering soft light",
        "default_time_of_day": "day",
        "environment_notes": "cafés, terraces, markets, rain-washed streets — intimate and warm",
        "expression_notes": "longing, shy smiles, tenderness, heartbreak",
    },
    "comedy": {
        "film_look": "bright comedic realism, punchy and colorful",
        "palette": "saturated cheerful colors, warm whites",
        "lighting": "even bright lighting, sunny exteriors",
        "default_time_of_day": "day",
        "environment_notes": "homes, offices, neighbourhoods — ordinary places, lively energy",
        "expression_notes": "exaggerated reactions, laughter, deadpan, surprise",
    },
    "mythology": {
        "film_look": "epic period drama, painterly grandeur",
        "palette": "royal golds, deep reds, temple stone, lush greens",
        "lighting": "grand natural light, torch-lit interiors",
        "default_time_of_day": "day",
        "environment_notes": "palaces, temples, forests, riverbanks — ancient India, ornate detail",
        "expression_notes": "devotion, valor, wrath, serenity",
    },
    "family_drama": {
        "film_look": "warm grounded drama, natural handheld feel",
        "palette": "earthy warm tones, home interiors, natural skin tones",
        "lighting": "soft daylight through windows, warm tungsten evenings",
        "default_time_of_day": "day",
        "environment_notes": "family homes, kitchens, courtyards — lived-in and real",
        "expression_notes": "affection, conflict, guilt, reconciliation",
    },
    "drama": {
        "film_look": "cinematic photorealistic drama, 35mm film",
        "palette": "true-to-life natural colors",
        "lighting": "natural, motivated by real time of day",
        "default_time_of_day": "day",
        "environment_notes": "real Indian locations matching the script beats",
        "expression_notes": "authentic emotion matching each dialogue beat",
    },
}


def _script_text(package: dict[str, Any]) -> str:
    parts: list[str] = [str(package.get("title") or "")]
    bible = package.get("bible") or {}
    parts.append(json.dumps(bible.get("characters") or [], ensure_ascii=False))
    for part in package.get("parts") or []:
        if part.get("screenplay"):
            parts.append(part["screenplay"])
    return "\n".join(parts)


def heuristic_style_guide(package: dict[str, Any]) -> dict[str, str]:
    """Keyword-based genre detection — no LLM required.

    Scores every genre by keyword hit count so a crime script with one
    'shadow' in the title doesn't get classified as horror.
    """
    text = _script_text(package)
    scores = {
        name: len(re.findall(pattern, text, re.I))
        for name, pattern in _GENRE_KEYWORDS
    }
    genre = max(scores, key=scores.get) if any(scores.values()) else "drama"
    guide = {"genre": genre, "era_setting": "modern-day India", **_GENRE_PRESETS[genre]}
    log.info("story_style_heuristic genre=%s scores=%s", genre, scores)
    return guide


def analyze_story_style(package: dict[str, Any]) -> dict[str, str]:
    """LLM analysis of the script → style guide; heuristic fallback."""
    fallback = heuristic_style_guide(package)
    try:
        from app.integrations.gemini.text import generate_json

        prompt = f"""You are a film colorist + production designer. Read this audio-drama
script and output the VISUAL STYLE GUIDE that truthfully matches the story.

CRITICAL: the look must come from the STORY, not from habit. A cricket /
school / family story is bright daylight with open, true-to-life color. Only
genuinely dark stories (horror, night-time crime) get low-key looks — and even
those must be bright in daytime or clinical interiors (labs, offices).

SCRIPT:
{_script_text(package)[:6000]}

Return ONLY JSON:
{{
 "genre": "sports|crime_thriller|horror|romance|comedy|mythology|family_drama|drama",
 "era_setting": "place + period, specific",
 "film_look": "one-line cinematography style",
 "palette": "dominant colors, truthful to the story world",
 "lighting": "how scenes are lit; vary day vs night; never 'always dark'",
 "default_time_of_day": "day|evening|night — when MOST of the story happens",
 "environment_notes": "typical locations and how they should feel",
 "expression_notes": "the emotional register actors should show"
}}"""
        raw = generate_json(prompt)
        guide = {k: str(v) for k, v in raw.items() if isinstance(v, (str, int, float)) and str(v).strip()}
        merged = {**fallback, **guide}
        log.info("story_style_llm genre=%s tod=%s", merged.get("genre"), merged.get("default_time_of_day"))
        return merged
    except Exception as exc:  # noqa: BLE001
        log.warning("story_style_llm_failed err=%s — using heuristic", exc)
        return fallback
