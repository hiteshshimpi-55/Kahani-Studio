"""Prompt builders for the visual pipeline.

Every prompt is grounded in the STORY STYLE GUIDE (genre, palette,
lighting, time of day) derived from the script itself — a cricket story
renders bright daylight, a horror story renders dark. RAG shot templates
steer framing; hard rules force multi-character coverage whenever people
are physically co-located.
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
   Examples: teammates in a dressing room before the final over;
   doctor + inspector + junior officer at a forensic table;
   the whole family around the dining table during the argument.

E. REVEAL / PRESENTATION BEATS
   When one character shows or explains something to others (coach's plan,
   expert's findings, a family secret): at least ONE shot must be group or
   two_shot with the presenter + listeners + the object of attention ON
   SCREEN together. Never show only the presenter's face while listeners
   are "off-screen".

F. SHOT SIZES
   establishing_wide | wide | medium | two_shot | ots | close_up |
   extreme_close_up | insert | group
   MCU (medium) = default single. CU only on emotional peaks. ECU ≤1/episode.

G. 180° RULE
   Character A always faces screen-RIGHT, B faces screen-LEFT within a scene.

H. PACING
   4–8s typical; 2.5–4s action; 8–11s reflective. Tile full audio duration.

I. CAMERA
   motion: slow_push_in | slow_pull_out | pan_left | pan_right | static
   angle:  eye | low | high | overhead | pov | dutch
   Vary both — do not repeat the same motion more than twice in a row, and
   do not put every shot at eye level. Low angle for power/heroics, high
   for vulnerability, overhead for geography, pov for immersion,
   dutch (sparingly) for unease.

J. WARDROBE
   Same outfit for a story_day; change only when the day changes.

K. NARRATOR
   Never on screen (voice-of-god). Use scenery, inserts, or the characters
   the narration is about — if narration describes people together, SHOW them together.

L. LIGHT FOLLOWS THE STORY
   time_of_day comes from the SCRIPT, not from genre habit. A morning
   match is bright sun; a night chase is dark. Interiors like labs,
   offices, and classrooms are lit bright and functional even in dark
   stories. NEVER make every scene dark by default.
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
    style_guide: dict[str, Any] | None = None,
) -> str:
    bible = package.get("bible") or {}
    templates_block = _format_templates(retrieved_templates or [])
    scenes_block = json.dumps(scene_hints or [], ensure_ascii=False, indent=1)
    style_block = json.dumps(style_guide or {}, ensure_ascii=False, indent=1)

    return f"""You are the GENERIC VISUAL DIRECTOR for a Pocket FM / Kuku TV–style
vertical (9:16) audio-drama studio. This pipeline runs for ANY script and ANY
genre after audiobook audio exists. You do NOT invent coverage from scratch —
you SELECT and ADAPT shot templates from the retrieved catalog, then fill in
story-specific action, wardrobe, expressions, and blocking.

{FILM_GRAMMAR_RULES}

STORY STYLE GUIDE (analysed from the script — your final style MUST agree
with this; refine wording but never contradict the genre or time of day):
{style_block}

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
 "style": {{"genre": str, "era_setting": str, "film_look": str, "palette": str, "lighting": str}},
 "characters": [{{"id": "SPEAKER_ID_UPPERCASE", "name": str,
   "appearance": "very specific face/age/build/hair — permanent",
   "wardrobe": {{"day1": "full outfit with fabrics/colors"}},
   "facing": "right"|"left"}}],
 "scenes": [{{"scene_id": "s1", "location": "rich specific place",
   "time_of_day": "as written in the SCRIPT for this beat",
   "story_day": "day1", "weather": str|null, "mood": str}}],
 "shots": [{{"shot_id": "sh01", "scene_id": "s1",
   "t_start": float, "t_end": float,
   "shot_size": "establishing_wide"|"wide"|"medium"|"two_shot"|"ots"|"close_up"|"extreme_close_up"|"insert"|"group",
   "characters_on_screen": ["SPEAKER_ID", ...],
   "action": "concrete present-tense what is VISIBLE — if people are together, name them ALL in the action",
   "expression": "each on-screen character's facial emotion for this beat",
   "camera_motion": "slow_push_in"|"slow_pull_out"|"pan_left"|"pan_right"|"static",
   "camera_angle": "eye"|"low"|"high"|"overhead"|"pov"|"dutch",
   "seq_ids": [..]}}]
}}

HARD CONSTRAINTS:
1. character.id MUST be the SPEAKER id from the transcript in UPPERCASE
   (e.g. INSPECTOR_MEHRA, VIKRAM, DR_KAPOOR). Never lowercase. Never narrator.
2. Shots tile [0, duration] contiguously.
3. For every co-located multi-character scene: include ≥1 two_shot OR group,
   plus OTS coverage. characters_on_screen must list EVERY person visible.
4. STYLE = STORY. Copy the genre/palette/lighting direction from the STORY
   STYLE GUIDE. Scene time_of_day must match the script beat. Bright story
   beats stay bright; functional interiors (lab, office, classroom) are lit
   bright and clean even inside dark genres.
5. Establishing shots before a character enters MUST be empty — no
   silhouettes or invented people.
6. Never write "off-screen" for someone who is in that scene's location.
7. Prefer the RETRIEVED SHOT TEMPLATES: copy their shot_size + camera_motion
   and paraphrase COMPOSE into action. Do not invent random coverage.
8. Vehicle departures/travel: prefer POV through the windshield or an
   exterior vehicle shot — not a fashion portrait of the hero standing still.
9. series_id is "{series_id}" — omit from JSON.
"""


_TOD_LIGHT = (
    (("morning", "sunrise", "dawn", "सुबह"), "Bright fresh morning light, long soft shadows, clear visibility."),
    (("noon", "afternoon", "day", "daytime", "दिन", "दोपहर"), "Bright natural daylight, open sun, true-to-life vivid colors, everything clearly visible."),
    (("evening", "sunset", "dusk", "golden", "शाम"), "Warm golden-hour light, amber sky, gentle contrast."),
    (("night", "midnight", "रात"), "Night scene with motivated practical lights — faces still clearly lit and readable, never murky."),
)

_ANGLE_TEXT = {
    "eye": "Camera at eye level, natural film blocking.",
    "low": "Low-angle shot looking up at the subject — powerful, heroic framing.",
    "high": "High-angle shot looking down — subject appears small or vulnerable.",
    "overhead": "Top-down overhead shot showing the spatial geography of the scene.",
    "pov": "First-person POV shot — the camera sees exactly what the character sees.",
    "dutch": "Slight dutch tilt for unease, horizon subtly canted.",
}


def _lighting_for(scene: SceneSpec) -> str:
    tod = (scene.time_of_day or "").lower()
    for keys, text in _TOD_LIGHT:
        if any(k in tod for k in keys):
            return text
    return "Natural lighting motivated by the location and time of day."


def style_suffix(plan: EpisodeVisualPlan) -> str:
    s = plan.style
    return (
        f" Style: {s.genre} story — {s.film_look}, {s.palette} palette,"
        f" {s.lighting}, {s.era_setting}. Photorealistic real photography,"
        f" natural skin texture, true colors. Vertical 9:16 cinematic frame."
        f" Absolutely no text, captions, subtitles, watermarks, logos, badges with"
        f" lettering, name tags, or readable writing anywhere in the image."
    )


def build_lookbook_prompt(char: CharacterLook, plan: EpisodeVisualPlan, story_day: str) -> str:
    outfit = char.wardrobe.get(story_day) or next(iter(char.wardrobe.values()), "story-appropriate clothing")
    return (
        f"Character reference sheet, one person only: {char.appearance}. "
        f"Wearing {outfit}. Standing, relaxed neutral pose, facing camera in a "
        f"three-quarter view, full body visible head to shoes, plain dark charcoal "
        f"studio background, even soft lighting, photorealistic Indian casting. "
        f"Plain clothing only — no embroidered words, no agency names on coats, "
        f"no patches with letters."
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
    empty = (
        "No people in frame — environment only. "
        if not who and shot.shot_size in ("establishing_wide", "wide", "insert")
        else ""
    )
    lab_note = ""
    loc = (scene.location or "").lower()
    if "lab" in loc or "forensic" in loc:
        lab_note = (
            "Bright sterile forensic lab, cool fluorescent lighting, clean metal "
            "tables, clinical — NOT a dark horror hallway. "
        )
    expression = f"EXPRESSIONS: {shot.expression}. " if (shot.expression or "").strip() and who else ""
    angle_text = _ANGLE_TEXT.get(shot.camera_angle, _ANGLE_TEXT["eye"])
    return (
        f"Cinematic film still, {size_text}. LOCATION: {scene.location}, "
        f"{scene.time_of_day}{weather}, {scene.mood} mood. "
        f"{_lighting_for(scene)} "
        f"{lab_note}{empty}{cast_text}{expression}"
        f"ACTION (follow exactly): {shot.action} "
        f"{angle_text} Match reference faces exactly. "
        f"Compose for a vertical 9:16 crop: keep all faces and key subjects in "
        f"the central area — the outer 15% of the left and right edges will be "
        f"cropped away."
        + style_suffix(plan)
    )
