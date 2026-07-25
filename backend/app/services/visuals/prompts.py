"""Prompt builders for the visual pipeline.

Director is RAG-backed: retrieved shot templates from the vector catalog
steer framing. Hard rules force multi-character coverage whenever people
are physically co-located (no more lonely singles in a crowded lab).
"""

from __future__ import annotations

import json
from typing import Any

from app.schemas.visuals import CharacterLook, EpisodeVisualPlan, SceneSpec, ShotSpec

FILM_GRAMMAR_RULES = """\
FILM GRAMMAR + HARD COVERAGE RULES (non-negotiable):

A. SCENE FIRST
   Split the episode into SCENES by LOCATION change. Every new location
   opens with exactly one ESTABLISHING WIDE.

B. CO-LOCATED vs REMOTE
   - REMOTE (phone / radio / separate rooms): singles + inserts are OK.
   - CO-LOCATED (same physical room/location): you MUST put multiple
     characters in the same frame. Forbidden: writing "off-screen" for a
     character who is in that location.

C. TWO PEOPLE IN SAME LOCATION
   Coverage mix for that scene MUST include:
     - at least ONE two_shot (both waist-up, relationship clear)
     - alternating OTS of each speaker (foreground shoulder of the other)
     - singles only AFTER the two_shot / OTS geography is established
   Target: ≥40% of shots in that scene are two_shot or ots.

D. THREE OR MORE IN SAME LOCATION
   Open with a GROUP shot showing ALL of them, then OTS / singles.
   Example: doctor + inspector + junior officer at a forensic table with
   the body/evidence visible → GROUP first, then OTS doctor→police,
   then reaction.

E. FORENSIC / REVEAL BEATS
   If a doctor/expert presents findings to police: at least ONE shot must
   be group or two_shot with doctor + police(s) + body/evidence ON SCREEN
   together. Never show only the doctor's face while police are "off-screen".

F. SHOT SIZES
   establishing_wide | wide | medium | two_shot | ots | close_up |
   extreme_close_up | insert | group
   MCU (medium) = default single. CU only on emotional peaks. ECU ≤1/episode.

G. 180° RULE
   Character A always faces screen-RIGHT, B faces screen-LEFT within a scene.

H. PACING
   4–8s typical; 2.5–4s action; 8–11s reflective. Tile full audio duration.

I. CAMERA MOTION
   slow_push_in | slow_pull_out | pan_left | pan_right | static
   Do not repeat the same motion more than twice in a row.

J. WARDROBE
   Same outfit for a story_day; change only when the day changes.

K. NARRATOR
   Never on screen (voice-of-god). Use scenery, inserts, or the characters
   the narration is about — if narration describes people together, SHOW them together.
"""


def _format_templates(templates: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for t in templates:
        lines.append(
            f"- [{t.get('slug')}] size={t.get('shot_size')} motion={t.get('camera_motion')} "
            f"chars={t.get('min_chars')}-{t.get('max_chars')}: {t.get('name')}\n"
            f"  WHEN: {t.get('when')}\n"
            f"  COMPOSE: {t.get('composition')}"
        )
    return "\n".join(lines) if lines else "(no templates retrieved)"


def build_director_prompt(
    package: dict[str, Any],
    timed_transcript: str,
    series_id: str,
    *,
    retrieved_templates: list[dict[str, Any]] | None = None,
    scene_hints: list[dict[str, Any]] | None = None,
) -> str:
    bible = package.get("bible") or {}
    templates_block = _format_templates(retrieved_templates or [])
    scenes_block = json.dumps(scene_hints or [], ensure_ascii=False, indent=1)

    return f"""You are the GENERIC VISUAL DIRECTOR for a Pocket FM / Kuku TV–style
vertical (9:16) audio-drama studio. This pipeline runs for ANY script after
audiobook audio exists. You do NOT invent coverage from scratch — you SELECT
and ADAPT shot templates from the retrieved catalog, then fill in story-specific
action, wardrobe, and blocking.

{FILM_GRAMMAR_RULES}

EPISODE TITLE: {package.get("title")}
LANGUAGE: {package.get("language")}
CHARACTER BIBLE (invent specific photoreal Indian-context physical looks):
{json.dumps(bible.get("characters", []), ensure_ascii=False, indent=1)}

PRE-EXTRACTED SCENE HINTS (use these scene_ids / locations; refine if needed):
{scenes_block}

TIMED AUDIO TRANSCRIPT (seq_id [t_start-t_end] SPEAKER (direction): text):
{timed_transcript}

RETRIEVED SHOT TEMPLATES (RAG — pick the best matching ones for each beat;
prefer multi-character templates whenever people share a location):
{templates_block}

Return ONLY JSON:
{{
 "style": {{"era_setting": str, "film_look": str, "palette": str, "lighting": str}},
 "characters": [{{"id": "SPEAKER_ID_UPPERCASE", "name": str,
   "appearance": "very specific face/age/build/hair — permanent",
   "wardrobe": {{"day1": "full outfit with fabrics/colors"}},
   "facing": "right"|"left"}}],
 "scenes": [{{"scene_id": "s1", "location": "rich specific place",
   "time_of_day": str, "story_day": "day1", "weather": str|null, "mood": str}}],
 "shots": [{{"shot_id": "sh01", "scene_id": "s1",
   "t_start": float, "t_end": float,
   "shot_size": "establishing_wide"|"wide"|"medium"|"two_shot"|"ots"|"close_up"|"extreme_close_up"|"insert"|"group",
   "characters_on_screen": ["SPEAKER_ID", ...],
   "action": "concrete present-tense what is VISIBLE — if people are together, name them ALL in the action",
   "camera_motion": "slow_push_in"|"slow_pull_out"|"pan_left"|"pan_right"|"static",
   "seq_ids": [..]}}]
}}

HARD CONSTRAINTS:
1. character.id MUST be the SPEAKER id from the transcript in UPPERCASE
   (e.g. INSPECTOR_MEHRA, VIKRAM, DR_KAPOOR). Never lowercase. Never narrator.
2. Shots tile [0, duration] contiguously.
3. For every co-located multi-character scene: include ≥1 two_shot OR group,
   plus OTS coverage. characters_on_screen must list EVERY person visible.
4. Lab / forensic / "showing the body" beats: mandatory group or two_shot with
   doctor + police + body/evidence all visible.
5. Phone-only beats: singles OK; do not invent a second person in the room.
6. Never write "off-screen" for someone who is in that scene's location.
7. series_id is "{series_id}" — omit from JSON.
"""


def style_suffix(plan: EpisodeVisualPlan) -> str:
    s = plan.style
    return (
        f" Style: {s.film_look}, {s.palette} palette, {s.lighting} lighting,"
        f" {s.era_setting}. Vertical 9:16 cinematic frame."
        f" Absolutely no text, captions, watermarks or logos in the image."
    )


def build_lookbook_prompt(char: CharacterLook, plan: EpisodeVisualPlan, story_day: str) -> str:
    outfit = char.wardrobe.get(story_day) or next(iter(char.wardrobe.values()), "story-appropriate clothing")
    return (
        f"Character reference sheet, one person only: {char.appearance}. "
        f"Wearing {outfit}. Standing, relaxed neutral pose, facing camera in a "
        f"three-quarter view, full body visible head to shoes, plain dark charcoal "
        f"studio background, even soft lighting, photorealistic."
        + style_suffix(plan)
    )


def build_shot_prompt(
    shot: ShotSpec,
    scene: SceneSpec,
    plan: EpisodeVisualPlan,
    ref_order: list[CharacterLook],
) -> str:
    size_text = {
        "establishing_wide": "extreme wide establishing shot, environment dominates the frame",
        "wide": "wide shot, full figures visible in the environment",
        "medium": "medium close-up, chest up",
        "two_shot": "two-shot from the waist up, BOTH characters clearly visible and interacting in the same frame",
        "ots": "over-the-shoulder shot: foreground shoulder of one character, face of the other clear",
        "close_up": "close-up, face fills the frame, every micro-expression visible",
        "extreme_close_up": "extreme close-up on the eyes or key object",
        "insert": "insert detail shot of the key object, shallow focus",
        "group": "group shot with ALL listed characters visible together, spatial arrangement clear",
    }.get(shot.shot_size, "medium shot")

    who = []
    for i, char in enumerate(ref_order, start=1):
        outfit = char.wardrobe.get(scene.story_day) or next(iter(char.wardrobe.values()), "")
        who.append(
            f"the person from reference image {i} ({char.name}: {char.appearance}, "
            f"wearing {outfit}, facing screen-{char.facing})"
        )
    cast_text = (
        "Characters in frame (ALL must appear, faces match references EXACTLY): "
        + "; ".join(who)
        + ". "
    ) if who else ""

    weather = f", {scene.weather}" if scene.weather else ""
    return (
        f"Cinematic film still, {size_text}. LOCATION: {scene.location}, "
        f"{scene.time_of_day}{weather}, {scene.mood} mood. "
        f"{cast_text}"
        f"ACTION: {shot.action} "
        f"Camera at eye level, natural film blocking."
        + style_suffix(plan)
    )
