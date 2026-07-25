"""Script Writer — single-episode outline → expand via LLM_PROVIDER, with stub fallback."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.integrations.llm import chat_completion, resolve_llm_settings

logger = logging.getLogger(__name__)

SCREENPLAY_HINT = """
Screenplay format (one beat per block):
SPEAKER: [direction] dialogue or narration text
[sfx: short concrete cue]

Example:
NARRATOR: [suspenseful] रात के दो बज रहे थे। मुंबई की बारिश थमने का नाम नहीं ले रही थी...
[sfx: phone ringing in dark room]
INSPECTOR_MEHRA: [firm, commanding] बोलो विक्रम। इस वक़्त फ़ोन का मतलब — कुछ बड़ा हुआ है।
"""

CRAFT_RULES = """
Craft rules for ONE episode (Pocket FM–style serial):
- Write exactly ONE part. Dense pacing for the target duration (default ~60–90s spoken).
- Multicast: NARRATOR guides; characters speak in voice; use SPEAKER ids from bible.name (UPPER_SNAKE).
- Every spoken line: SPEAKER: [emotion/direction] text — never bare dialogue.
- Place 3–6 concrete [sfx: ...] cues that match the action (phone, rain, footsteps, thunder, etc.).
- Mirror sfx into parts[0].sfx_cues as plain strings (no "sfx:" prefix).
- Language: match the user's prompt (hi or en). Hindi should feel serial-thriller vernacular, not textbook.
- End with a hard cliff_out (one sentence hook for the next episode).
- Prefer short punchy exchanges + narrator bridges over long speeches.
- If Series cast is provided in SOURCE, REUSE those character ids/names/voices; only add new characters when the story needs them.
"""

GOLDEN_EXAMPLE = """
Golden reference (shape + density — do not copy plot):
{
  "title": "काला साया — Episode 3: गुमशुदा सबूत",
  "language": "hi",
  "narration_config": {
    "pov": "third_limited",
    "cast_model": "multicast",
    "platform_style": "pocket_fm_serial",
    "soundscape": true,
    "narrators": [{"id": "NARRATOR", "voice_notes": "intense thriller narrator, measured suspense, male"}]
  },
  "bible": {
    "characters": [
      {"id": "narrator", "name": "NARRATOR", "role": "guide", "voice": "intense male narrator, measured suspense", "speech_patterns": "measured, suspenseful, dramatic pauses", "arc": "guides the investigation"},
      {"id": "inspector_mehra", "name": "INSPECTOR_MEHRA", "role": "protagonist", "voice": "mature commanding male", "speech_patterns": "firm, clipped", "arc": "veteran closing in"},
      {"id": "vikram", "name": "VIKRAM", "role": "ally", "voice": "young sharp male, tense", "speech_patterns": "urgent, quick reports", "arc": "junior finding shocks"}
    ]
  },
  "parts": [{
    "part_number": 3,
    "title": "गुमशुदा सबूत",
    "target_duration_sec": 60,
    "screenplay": "NARRATOR: [suspenseful] ...\\n\\n[sfx: phone ringing in dark room]\\n\\nINSPECTOR_MEHRA: [firm, commanding] ...",
    "cliff_out": "गवाह का झूठ पकड़ा गया — लेकिन असली ख़तरा अभी सामने आना बाक़ी है।",
    "sfx_cues": ["phone ringing in dark room", "car engine starting in rain", "thunder rumble close"]
  }],
  "total_duration_sec": 60
}
"""


def default_narration_config() -> dict[str, Any]:
    return {
        "pov": "third_limited",
        "cast_model": "multicast",
        "platform_style": "pocket_fm_serial",
        "soundscape": True,
        "narrators": [{"id": "NARRATOR", "voice_notes": "intense thriller narrator, measured suspense"}],
    }


def render_screenplay_from_package(package: dict[str, Any]) -> str:
    parts = package.get("parts") or []
    blocks: list[str] = []
    title = package.get("title") or "Untitled"
    blocks.append(f"# {title}")
    blocks.append("")
    for part in parts:
        part_no = part.get("part_number") or part.get("number") or "?"
        part_title = part.get("title") or f"Part {part_no}"
        blocks.append(f"## Part {part_no}: {part_title}")
        blocks.append("")
        screenplay = part.get("screenplay") or part.get("text") or ""
        if screenplay:
            blocks.append(screenplay.strip())
            blocks.append("")
        else:
            for beat in part.get("beats") or []:
                speaker = beat.get("speaker") or "NARRATOR"
                direction = beat.get("direction") or beat.get("emotion") or ""
                text = beat.get("text") or ""
                if direction:
                    blocks.append(f"{speaker}: [{direction}] {text}")
                else:
                    blocks.append(f"{speaker}: {text}")
            blocks.append("")
        cliff = part.get("cliff_out")
        if cliff:
            blocks.append(f"_Cliff:_ {cliff}")
            blocks.append("")
    return "\n".join(blocks).strip() + "\n"


_SFX_RE = re.compile(r"\[sfx:\s*([^\]]+)\]", re.IGNORECASE)


def normalize_script_package(
    package: dict[str, Any],
    *,
    narration_config: dict[str, Any],
    part_number: int,
    total_duration_sec: int,
) -> dict[str, Any]:
    """Light post-parse normalize: single part, duration, sfx_cues from screenplay."""
    package.setdefault("narration_config", narration_config)
    package.setdefault("title", "Untitled")
    package["total_duration_sec"] = int(
        package.get("total_duration_sec") or total_duration_sec
    )

    bible = package.get("bible") if isinstance(package.get("bible"), dict) else {}
    chars = bible.get("characters") if isinstance(bible.get("characters"), list) else []
    package["bible"] = {"characters": chars}

    parts = package.get("parts") if isinstance(package.get("parts"), list) else []
    if not parts:
        parts = [
            {
                "part_number": part_number,
                "title": package.get("title") or f"Episode {part_number}",
                "target_duration_sec": total_duration_sec,
                "screenplay": "",
                "cliff_out": "",
                "sfx_cues": [],
            }
        ]
    else:
        # Enforce single episode — keep first part only
        parts = [parts[0]]

    part = parts[0] if isinstance(parts[0], dict) else {}
    part["part_number"] = int(part.get("part_number") or part_number)
    part["target_duration_sec"] = int(
        part.get("target_duration_sec") or total_duration_sec
    )
    screenplay = str(part.get("screenplay") or "").strip()
    part["screenplay"] = screenplay

    found_sfx = [m.strip() for m in _SFX_RE.findall(screenplay) if m.strip()]
    cues = part.get("sfx_cues") if isinstance(part.get("sfx_cues"), list) else []
    cues_norm = [str(c).strip() for c in cues if str(c).strip()]
    for cue in found_sfx:
        if cue not in cues_norm:
            cues_norm.append(cue)
    part["sfx_cues"] = cues_norm
    part.setdefault("cliff_out", "")
    part.setdefault("title", f"Episode {part['part_number']}")
    package["parts"] = [part]
    return package


class ScriptWriterAgent:
    def __init__(self) -> None:
        self.provider, self.api_key, self.model = resolve_llm_settings()

    async def write(
        self,
        *,
        source_md: str,
        narration_config: dict[str, Any],
        part_count: int = 1,
        total_duration_sec: int = 90,
        part_number: int = 1,
    ) -> tuple[dict[str, Any], str]:
        # Part-by-part: always one episode per run
        _ = part_count
        part_number = max(1, int(part_number or 1))
        total_duration_sec = max(30, min(180, int(total_duration_sec or 90)))

        if not self.api_key:
            package = self._stub_package(
                source_md=source_md,
                narration_config=narration_config,
                part_number=part_number,
                total_duration_sec=total_duration_sec,
            )
            return package, render_screenplay_from_package(package)

        try:
            package = await self._two_pass(
                source_md=source_md,
                narration_config=narration_config,
                part_number=part_number,
                total_duration_sec=total_duration_sec,
            )
            screenplay = render_screenplay_from_package(package)
            return package, screenplay
        except Exception:
            logger.exception(
                "Script writer failed (provider=%s model=%s); using stub",
                self.provider,
                self.model,
            )
            package = self._stub_package(
                source_md=source_md,
                narration_config=narration_config,
                part_number=part_number,
                total_duration_sec=total_duration_sec,
            )
            return package, render_screenplay_from_package(package)

    async def _two_pass(
        self,
        *,
        source_md: str,
        narration_config: dict[str, Any],
        part_number: int,
        total_duration_sec: int,
    ) -> dict[str, Any]:
        axes = json.dumps(narration_config, ensure_ascii=False)
        system = (
            "You are an enterprise audio showrunner for Pocket FM–style serials. "
            "You write ONE episode at a time with cinematic tension and concrete SFX. "
            "Respond with valid JSON only (no markdown fences)."
        )

        outline_prompt = f"""Outline ONE episode only (part_number={part_number}, ~{total_duration_sec}s spoken).

narration_config: {axes}

{CRAFT_RULES}

{SCREENPLAY_HINT}

Return JSON shape:
{{
  "title": "...",
  "language": "en"|"hi",
  "bible": {{"characters": [{{"id","name","role","voice","speech_patterns","arc"}}]}},
  "outline": {{
    "part_number": {part_number},
    "title": "...",
    "beats": ["hook", "turn", "reveal", "cliff"],
    "summary": "...",
    "cliff_out": "...",
    "target_duration_sec": {total_duration_sec}
  }}
}}

SOURCE:
{source_md[:24000]}
"""
        outline_text = await chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": outline_prompt},
            ],
            max_tokens=4096,
        )
        outline = self._parse_json(outline_text)

        expand_prompt = f"""Expand this outline into a full single-episode ScriptPackage JSON.

narration_config: {axes}
outline: {json.dumps(outline, ensure_ascii=False)[:12000]}

{CRAFT_RULES}

{SCREENPLAY_HINT}

{GOLDEN_EXAMPLE}

SOURCE:
{source_md[:20000]}

Return ONLY JSON:
{{
  "title": "...",
  "language": "hi"|"en",
  "narration_config": {{...}},
  "bible": {{"characters": [{{"id","name","role","voice","speech_patterns","arc"}}]}},
  "parts": [{{
    "part_number": {part_number},
    "title": "...",
    "target_duration_sec": {total_duration_sec},
    "screenplay": "full SPEAKER/[sfx] screenplay string",
    "cliff_out": "...",
    "sfx_cues": ["..."]
  }}],
  "total_duration_sec": {total_duration_sec}
}}
"""
        expand_text = await chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": expand_prompt},
            ],
            max_tokens=16000,
        )
        package = self._parse_json(expand_text)
        if not package.get("title"):
            package["title"] = outline.get("title") or f"Episode {part_number}"
        return normalize_script_package(
            package,
            narration_config=narration_config,
            part_number=part_number,
            total_duration_sec=total_duration_sec,
        )

    def _stub_package(
        self,
        *,
        source_md: str,
        narration_config: dict[str, Any],
        part_number: int,
        total_duration_sec: int,
    ) -> dict[str, Any]:
        prompt_line = next(
            (ln.strip() for ln in source_md.splitlines() if ln.strip() and not ln.startswith("#")),
            "A mysterious story unfolds.",
        )
        # Prefer Hindi stub when Devanagari appears in the brief
        use_hi = bool(re.search(r"[\u0900-\u097F]", source_md)) or "hindi" in source_md.lower()
        if use_hi:
            title = f"एपिसोड {part_number}"
            screenplay = (
                f"NARRATOR: [suspenseful] रात गहरी थी। {prompt_line}\n\n"
                f"[sfx: distant thunder]\n\n"
                f"RIYA: [nervous, whispering] कुछ गलत लग रहा है…\n\n"
                f"ARJUN: [steady, firm] रुको। हम एक साथ चलते हैं।\n\n"
                f"[sfx: floorboard creak]\n\n"
                f"NARRATOR: [ominous] लेकिन जो इंतज़ार कर रहा था… वो अभी सामने आने वाला था।"
            )
            cliff = "सच का दरवाज़ा खुला — और उसके पीछे कुछ और भी छुपा था।"
            lang = "hi"
        else:
            title = f"Episode {part_number}"
            screenplay = (
                f"NARRATOR: [suspenseful] Night held its breath. {prompt_line}\n\n"
                f"[sfx: distant thunder]\n\n"
                f"RIYA: [nervous, whispering] Something feels wrong…\n\n"
                f"ARJUN: [steady, firm] Stay close. We keep moving.\n\n"
                f"[sfx: floorboard creak]\n\n"
                f"NARRATOR: [ominous] And whatever waited for them… was already listening."
            )
            cliff = "The door opened — and what stood behind it was not the answer."
            lang = "en"

        package = {
            "title": title,
            "language": lang,
            "narration_config": narration_config,
            "bible": {
                "characters": [
                    {
                        "id": "narrator",
                        "name": "NARRATOR",
                        "role": "guide",
                        "voice": "intense thriller narrator, measured suspense",
                        "speech_patterns": "measured, suspenseful, dramatic pauses",
                        "arc": "guides through the dark turn",
                    },
                    {
                        "id": "riya",
                        "name": "RIYA",
                        "role": "protagonist",
                        "voice": "young tense female, breathless urgency",
                        "speech_patterns": "short bursts, nervous",
                        "arc": "from fear to resolve",
                    },
                    {
                        "id": "arjun",
                        "name": "ARJUN",
                        "role": "ally",
                        "voice": "steady protective male",
                        "speech_patterns": "reassuring, clipped",
                        "arc": "protector under pressure",
                    },
                ]
            },
            "parts": [
                {
                    "part_number": part_number,
                    "title": title,
                    "target_duration_sec": total_duration_sec,
                    "screenplay": screenplay,
                    "cliff_out": cliff,
                    "sfx_cues": ["distant thunder", "floorboard creak"],
                }
            ],
            "total_duration_sec": total_duration_sec,
            "stub": True,
        }
        return normalize_script_package(
            package,
            narration_config=narration_config,
            part_number=part_number,
            total_duration_sec=total_duration_sec,
        )

    def _parse_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        return json.loads(text)
