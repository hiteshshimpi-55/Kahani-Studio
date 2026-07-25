"""Script Writer — two-pass outline → expand via LLM_PROVIDER, with stub fallback."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.integrations.llm import chat_completion, resolve_llm_settings

logger = logging.getLogger(__name__)

SCREENPLAY_HINT = """
Screenplay format (one line per beat):
SPEAKER: [direction] dialogue or narration text

Example:
NARRATOR: [calm, measured] The house waited in the dark.
RIYA: [nervous, whispering] Are you sure about this?
"""


def default_narration_config() -> dict[str, Any]:
    return {
        "pov": "third_limited",
        "cast_model": "multicast",
        "platform_style": "pocket_fm_serial",
        "soundscape": True,
        "narrators": [{"id": "NARRATOR", "voice_notes": "calm thriller guide"}],
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


class ScriptWriterAgent:
    def __init__(self) -> None:
        self.provider, self.api_key, self.model = resolve_llm_settings()

    async def write(
        self,
        *,
        source_md: str,
        narration_config: dict[str, Any],
        part_count: int = 4,
        total_duration_sec: int = 600,
    ) -> tuple[dict[str, Any], str]:
        if not self.api_key:
            package = self._stub_package(
                source_md=source_md,
                narration_config=narration_config,
                part_count=part_count,
                total_duration_sec=total_duration_sec,
            )
            return package, render_screenplay_from_package(package)

        try:
            package = await self._two_pass(
                source_md=source_md,
                narration_config=narration_config,
                part_count=part_count,
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
                part_count=part_count,
                total_duration_sec=total_duration_sec,
            )
            return package, render_screenplay_from_package(package)

    async def _two_pass(
        self,
        *,
        source_md: str,
        narration_config: dict[str, Any],
        part_count: int,
        total_duration_sec: int,
    ) -> dict[str, Any]:
        axes = json.dumps(narration_config, ensure_ascii=False)
        system = (
            "You are an enterprise audio showrunner for Pocket FM–style serials. "
            "Respond with valid JSON only (no markdown fences)."
        )

        outline_prompt = f"""Write a JSON outline only for a {part_count}-part script totaling ~{total_duration_sec}s.

narration_config: {axes}

{SCREENPLAY_HINT}

Return JSON shape:
{{
  "title": "...",
  "language": "en"|"hi",
  "bible": {{"characters": [{{"id","name","role","voice","speech_patterns","arc"}}]}},
  "outline_parts": [{{"part_number", "title", "summary", "cliff_out", "target_duration_sec"}}]
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

        expand_prompt = f"""Expand this outline into a full ScriptPackage JSON.
Each part must include a "screenplay" string in SPEAKER: [direction] text format.
Include narration_config echo, bible, and parts with cliff_out and sfx_cues.

narration_config: {axes}
outline: {json.dumps(outline, ensure_ascii=False)[:12000]}

SOURCE:
{source_md[:20000]}

Return ONLY JSON:
{{
  "title": "...",
  "language": "...",
  "narration_config": {{...}},
  "bible": {{...}},
  "parts": [{{"part_number","title","target_duration_sec","screenplay","cliff_out","sfx_cues":[]}}],
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
        package.setdefault("narration_config", narration_config)
        package.setdefault("title", outline.get("title") or "Untitled")
        return package

    def _stub_package(
        self,
        *,
        source_md: str,
        narration_config: dict[str, Any],
        part_count: int,
        total_duration_sec: int,
    ) -> dict[str, Any]:
        prompt_line = next(
            (ln.strip() for ln in source_md.splitlines() if ln.strip() and not ln.startswith("#")),
            "A mysterious story unfolds.",
        )
        per = max(60, total_duration_sec // max(part_count, 1))
        parts = []
        for i in range(1, part_count + 1):
            screenplay = (
                f"NARRATOR: [calm, measured] Part {i}. {prompt_line}\n\n"
                f"RIYA: [tense] Something feels wrong here.\n\n"
                f"ARJUN: [steady] Stay close. We keep moving.\n\n"
                f"NARRATOR: [low, ominous] The silence answers them."
            )
            parts.append(
                {
                    "part_number": i,
                    "title": f"Beat {i}",
                    "target_duration_sec": per,
                    "screenplay": screenplay,
                    "cliff_out": "A door creaks open where none should.",
                    "sfx_cues": ["distant wind", "floorboard creak"],
                }
            )
        return {
            "title": "Generated Stub Script",
            "language": "en",
            "narration_config": narration_config,
            "bible": {
                "characters": [
                    {
                        "id": "narrator",
                        "name": "NARRATOR",
                        "role": "guide",
                        "voice": "calm thriller",
                        "speech_patterns": "measured",
                        "arc": "omniscient limited guide",
                    },
                    {
                        "id": "riya",
                        "name": "RIYA",
                        "role": "protagonist",
                        "voice": "nervous",
                        "speech_patterns": "short bursts",
                        "arc": "from fear to resolve",
                    },
                    {
                        "id": "arjun",
                        "name": "ARJUN",
                        "role": "ally",
                        "voice": "steady",
                        "speech_patterns": "reassuring",
                        "arc": "protector under pressure",
                    },
                ]
            },
            "parts": parts,
            "total_duration_sec": total_duration_sec,
            "stub": True,
        }

    def _parse_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        return json.loads(text)
