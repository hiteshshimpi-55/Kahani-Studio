"""Generic Visual Director agent — script + timed audio → shot plan.

Pipeline:
  1. Extract scenes / co-located cast from ScriptPackage + timeline
  2. Retrieve shot templates (vector RAG, local fallback)
  3. Gemini plans characters + timed shots using those templates
  4. Validate & repair: force group/two_shot when co-located people were
     planned as lonely singles
  5. Heuristic fallback if LLM unavailable
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.integrations.gemini.text import generate_json
from app.integrations.visuals.templates import retrieve_shot_templates
from app.schemas.visuals import (
    CharacterLook,
    EpisodeVisualPlan,
    SceneSpec,
    ShotSpec,
    StyleSpec,
)
from app.services.visuals.prompts import build_director_prompt
from app.services.visuals.story_style import analyze_story_style

log = logging.getLogger(__name__)

_NARRATOR_ROLES = frozenset({"narrator", "guide"})
_LOCATION_HINTS = [
    (re.compile(r"लैब|lab|forensic|फ़ॉरेंसिक|पोस्टमॉर्टम|autopsy", re.I), "forensic laboratory"),
    (re.compile(r"stadium|मैदान|pitch|ground|क्रिकेट|match", re.I), "sports ground / stadium"),
    (re.compile(r"school|college|classroom|स्कूल|कॉलेज|कक्षा", re.I), "school / college"),
    (re.compile(r"office|दफ़्तर|ऑफ़िस|meeting", re.I), "office"),
    (re.compile(r"बाज़ार|market|दुकान|shop|mall", re.I), "market / shop"),
    (re.compile(r"मंदिर|temple|मस्जिद|church|गुरुद्वारा", re.I), "place of worship"),
    # Village / rural horror — before generic "street" so गाँव beats city road
    (
        re.compile(
            r"गाँव\s*की\s*सीमा|अजनबी\s*गाँव|village\s*boundary|empty\s*village|"
            r"सन्नाटा|खामोशी.*गाँव|गाँव.*खामोशी",
            re.I,
        ),
        "deserted Indian village outskirts — empty dirt road, no people, night wind",
    ),
    (
        re.compile(r"झोपड़ी|hut|cabin|दीपक\s*जल|lamp\s*flicker|oil\s*lamp", re.I),
        "lonely mud-thatch village hut with a flickering oil lamp in the doorway",
    ),
    (
        re.compile(r"footsteps on gravel|कच्चा\s*रास्ता|gravel|झोपड़ी की ओर", re.I),
        "gravel path through deserted village toward the hut",
    ),
    (re.compile(r"गाड़ी|car|jeep|सड़क|street|बारिश.*सड़क", re.I), "street / car travel"),
    (re.compile(r"कमरा|bedroom|फ़ोन|apartment|बेड", re.I), "bedroom / apartment"),
    (re.compile(r"रसोई|kitchen|आँगन|courtyard|dining|खाना", re.I), "family home interior"),
    (re.compile(r"अदालत|court(?!yard)", re.I), "courtroom"),
    (re.compile(r"थाना|police station|interrogat", re.I), "police station"),
]

def _timed_transcript(package: dict[str, Any], timeline: list[dict[str, Any]]) -> str:
    from app.services.audiobook.service import parse_screenplay

    screenplay = ""
    for part in package.get("parts") or []:
        if part.get("screenplay"):
            screenplay = part["screenplay"]
            break
    parsed = parse_screenplay(screenplay)
    text_by_seq: dict[str, tuple[str, str, str]] = {}
    for ev in parsed.events:
        if ev.line:
            text_by_seq[ev.line.seq_id] = (
                ev.line.speaker, ev.line.direction or "", ev.line.text,
            )

    rows: list[str] = []
    for ev in timeline:
        if ev["type"] == "line":
            speaker, direction, text = text_by_seq.get(
                ev["seq_id"], (ev.get("speaker", "?"), "", ""),
            )
            rows.append(
                f'{ev["seq_id"]} [{ev["t_start"]:.1f}-{ev["t_end"]:.1f}] '
                f'{speaker} ({direction}): {text}'
            )
        else:
            rows.append(
                f'{ev["seq_id"]} [{ev["t_start"]:.1f}-{ev["t_end"]:.1f}] '
                f'SFX: {ev.get("cue", "")}'
            )
    return "\n".join(rows)


def _on_screen_cast(package: dict[str, Any]) -> list[dict[str, Any]]:
    bible = (package.get("bible") or {}).get("characters") or []
    out = []
    for ch in bible:
        role = (ch.get("role") or "").lower()
        if role in _NARRATOR_ROLES:
            continue
        cid = (ch.get("name") or ch.get("id") or "").upper()
        if cid:
            out.append({**ch, "id": cid, "name": cid})
    return out


def extract_scene_hints(
    package: dict[str, Any],
    timeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Heuristic scene breakdown: location changes + who can be co-located."""
    from app.services.audiobook.service import parse_screenplay

    screenplay = ""
    for part in package.get("parts") or []:
        if part.get("screenplay"):
            screenplay = part["screenplay"]
            break
    parsed = parse_screenplay(screenplay)
    cast = _on_screen_cast(package)
    cast_ids = [c["id"] for c in cast]

    # Walk lines; start a new scene when location keywords change.
    scenes: list[dict[str, Any]] = []
    current_loc = "primary story location"
    current_speakers: set[str] = set()
    scene_idx = 0
    buf_text: list[str] = []

    def flush() -> None:
        nonlocal scene_idx, current_speakers, buf_text
        if not buf_text and not scenes:
            return
        scene_idx += 1
        # Phone-only if only one speaker and phone cues dominate
        joined = " ".join(buf_text)
        remote = bool(re.search(r"फ़ोन|phone|call|बोलो", joined, re.I)) and len(current_speakers) <= 1
        colocated = [] if remote else sorted(current_speakers)
        # Narration about "the family" / परिवार ⇒ whole on-screen cast is present
        if not remote and re.search(r"परिवार|family", joined, re.I):
            colocated = sorted(set(colocated) | set(cast_ids))
        # Carry companions across contiguous outdoor beats (journey / village walk)
        if (
            not remote
            and scenes
            and not scenes[-1].get("remote_dialogue")
            and scenes[-1].get("colocated_characters")
        ):
            colocated = sorted(set(colocated) | set(scenes[-1]["colocated_characters"]))
        # Forensic: all cast who appear later in lab context
        if re.search(r"lab|forensic|लैब|पोस्टमॉर्टम|ज़हर|body", joined, re.I):
            colocated = sorted(set(colocated) | set(cast_ids))
            remote = False
        scenes.append({
            "scene_id": f"s{scene_idx}",
            "location_hint": current_loc,
            "colocated_characters": colocated,
            "remote_dialogue": remote,
            "must_include_multi_character_frames": (not remote) and len(colocated) >= 2,
            "beat_summary": joined[:240],
        })
        current_speakers = set()
        buf_text = []

    for ev in parsed.events:
        chunk = ""
        speaker_to_add: str | None = None
        if ev.sfx_cue:
            chunk = ev.sfx_cue
        if ev.line:
            chunk = f"{ev.line.speaker}: {ev.line.text}"
            if ev.line.speaker.upper() not in ("NARRATOR", "GUIDE"):
                speaker_to_add = ev.line.speaker.upper()
        if not chunk:
            continue
        for rx, loc in _LOCATION_HINTS:
            if rx.search(chunk) and loc != current_loc:
                flush()
                current_loc = loc
                break
        # Add speaker after a location flush so they belong to the NEW scene.
        if speaker_to_add:
            current_speakers.add(speaker_to_add)
        buf_text.append(chunk)
    flush()

    if not scenes:
        scenes.append({
            "scene_id": "s1",
            "location_hint": current_loc,
            "colocated_characters": cast_ids,
            "remote_dialogue": False,
            "must_include_multi_character_frames": len(cast_ids) >= 2,
            "beat_summary": package.get("title") or "",
        })
    return scenes


def _retrieve_for_episode(
    package: dict[str, Any],
    scene_hints: list[dict[str, Any]],
    style_guide: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Pull a diverse template set covering the whole episode.

    Queries are built from the story itself (title + genre + scenes) —
    never hardcoded to one genre.
    """
    guide = style_guide or {}
    genre = guide.get("genre", "drama")
    queries = [
        f"{package.get('title', '')} {genre} vertical film coverage",
        f"{genre} {guide.get('environment_notes', '')[:120]} establishing wide",
        "two shot dialogue colocated conversation over the shoulder",
        "group shot everyone visible together reveal presentation",
        "single insert reaction close up emotional beat",
    ]
    for sc in scene_hints:
        q = (
            f"{sc.get('location_hint', '')} "
            f"{' '.join(sc.get('colocated_characters') or [])} "
            f"{sc.get('beat_summary', '')[:120]}"
        )
        if sc.get("must_include_multi_character_frames"):
            q += " group two_shot ots colocated both characters on screen"
        queries.append(q)

    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for q in queries:
        for t in retrieve_shot_templates(q, num_results=5):
            slug = t.get("slug") or ""
            if slug and slug not in seen:
                seen.add(slug)
                merged.append(t)
    return merged[:18]


def _snap_shots(shots: list[ShotSpec], duration: float) -> list[ShotSpec]:
    shots = sorted((s for s in shots if s.t_end > s.t_start), key=lambda s: s.t_start)
    if not shots:
        return shots
    cursor = 0.0
    fixed: list[ShotSpec] = []
    for i, s in enumerate(shots):
        s.t_start = round(cursor, 3)
        end = s.t_end if i < len(shots) - 1 else duration
        s.t_end = round(max(s.t_start + 0.5, min(end, duration)), 3)
        cursor = s.t_end
        fixed.append(s)
        if cursor >= duration:
            break
    if fixed:
        fixed[-1].t_end = round(duration, 3)
    return [s for s in fixed if s.duration >= 0.5]


def _normalize_character_ids(plan: EpisodeVisualPlan) -> None:
    for c in plan.characters:
        c.id = c.id.upper()
        c.name = (c.name or c.id).upper()
    for s in plan.shots:
        s.characters_on_screen = [x.upper() for x in s.characters_on_screen]


def _repair_multi_character_coverage(
    plan: EpisodeVisualPlan,
    scene_hints: list[dict[str, Any]],
) -> None:
    """If a co-located indoor scene has zero two_shot/group/ots, inject repairs.

    Never force multi-character frames onto remote phone beats or travel/car
    exteriors — those stay singles / inserts / wides.
    """
    hint_by_id = {h["scene_id"]: h for h in scene_hints}
    multi_sizes = {"two_shot", "ots", "group"}
    travel_space = re.compile(
        r"street\s*/\s*car|car travel|jeep|windshield|vehicle|बारिश.*सड़क|गाड़ी",
        re.I,
    )

    for scene in plan.scenes:
        loc = scene.location or ""
        hint = hint_by_id.get(scene.scene_id) or {}
        if hint.get("remote_dialogue"):
            continue
        if travel_space.search(loc):
            continue
        if not hint.get("must_include_multi_character_frames"):
            continue

        colocated = [c.upper() for c in (hint.get("colocated_characters") or [])]
        if len(colocated) < 2:
            colocated = [c.id for c in plan.characters[:3]]
        if len(colocated) < 2:
            continue

        scene_shots = [s for s in plan.shots if s.scene_id == scene.scene_id]
        if not scene_shots:
            continue
        has_multi = any(
            s.shot_size in multi_sizes and len(s.characters_on_screen) >= 2
            for s in scene_shots
        )
        if has_multi:
            continue

        # Prefer a mid/long shot that isn't establishing/insert
        candidates = [
            s for s in scene_shots
            if s.shot_size not in ("establishing_wide", "insert", "extreme_close_up")
        ] or scene_shots
        target = max(candidates, key=lambda s: s.duration)
        if len(colocated) >= 3:
            target.shot_size = "group"
            target.characters_on_screen = colocated[:4]
            target.action = (
                f"{', '.join(colocated)} together in {scene.location}, all "
                f"clearly visible and engaged with the focus of this beat. "
                f"{target.action}"
            )
        else:
            target.shot_size = "two_shot"
            target.characters_on_screen = colocated[:2]
            target.action = (
                f"{colocated[0]} and {colocated[1]} facing each other in "
                f"{scene.location}, both clearly visible. {target.action}"
            )
        target.camera_motion = "slow_push_in"
        log.info(
            "director_repair scene=%s promoted %s -> %s chars=%s",
            scene.scene_id, target.shot_id, target.shot_size, target.characters_on_screen,
        )


class VisualDirector:
    def plan(
        self,
        package: dict[str, Any],
        timeline: list[dict[str, Any]],
        duration: float,
        *,
        series_id: str,
        use_llm: bool = True,
    ) -> EpisodeVisualPlan:
        scene_hints = extract_scene_hints(package, timeline)
        style_guide = analyze_story_style(package)
        templates = _retrieve_for_episode(package, scene_hints, style_guide)
        log.info(
            "director_context scenes=%d templates=%d genre=%s sources=%s",
            len(scene_hints),
            len(templates),
            style_guide.get("genre"),
            sorted({t.get("source", "?") for t in templates}),
        )

        if use_llm:
            try:
                return self._plan_llm(
                    package, timeline, duration,
                    series_id=series_id,
                    scene_hints=scene_hints,
                    templates=templates,
                    style_guide=style_guide,
                )
            except Exception:
                log.exception("director_llm_failed — falling back to heuristic planner")
        return self._plan_heuristic(
            package, timeline, duration,
            series_id=series_id,
            scene_hints=scene_hints,
            style_guide=style_guide,
        )

    def _plan_llm(
        self,
        package: dict[str, Any],
        timeline: list[dict[str, Any]],
        duration: float,
        *,
        series_id: str,
        scene_hints: list[dict[str, Any]],
        templates: list[dict[str, Any]],
        style_guide: dict[str, Any] | None = None,
    ) -> EpisodeVisualPlan:
        prompt = build_director_prompt(
            package,
            _timed_transcript(package, timeline),
            series_id,
            retrieved_templates=templates,
            scene_hints=scene_hints,
            style_guide=style_guide,
        )
        raw = generate_json(prompt)
        style_fields = {
            k: v
            for k, v in {**(style_guide or {}), **(raw.get("style") or {})}.items()
            if k in StyleSpec.model_fields and v
        }
        plan = EpisodeVisualPlan(
            series_id=series_id,
            title=package.get("title"),
            language=package.get("language") or "hi",
            style=StyleSpec(**style_fields),
            characters=[CharacterLook(**c) for c in raw.get("characters") or []],
            scenes=[SceneSpec(**s) for s in raw.get("scenes") or []],
            shots=[ShotSpec(**s) for s in raw.get("shots") or []],
        )
        _normalize_character_ids(plan)
        plan.shots = _snap_shots(plan.shots, duration)
        _repair_multi_character_coverage(plan, scene_hints)
        if not plan.shots:
            raise ValueError("LLM plan contained no usable shots")
        multi = sum(1 for s in plan.shots if s.shot_size in ("two_shot", "ots", "group"))
        log.info(
            "director_llm_ok shots=%d multi_char_frames=%d scenes=%d characters=%d",
            len(plan.shots), multi, len(plan.scenes), len(plan.characters),
        )
        return plan

    def _plan_heuristic(
        self,
        package: dict[str, Any],
        timeline: list[dict[str, Any]],
        duration: float,
        *,
        series_id: str,
        scene_hints: list[dict[str, Any]],
        style_guide: dict[str, Any] | None = None,
    ) -> EpisodeVisualPlan:
        guide = style_guide or {}
        default_tod = guide.get("default_time_of_day") or "day"
        cast = _on_screen_cast(package)
        characters = [
            CharacterLook(
                id=c["id"],
                name=c["id"],
                appearance=f"Indian adult matching voice notes: {c.get('voice', '')}",
                wardrobe={"day1": "story-appropriate Indian clothing"},
                facing="right" if i % 2 == 0 else "left",
            )
            for i, c in enumerate(cast)
        ]
        scenes = [
            SceneSpec(
                scene_id=h["scene_id"],
                location=h.get("location_hint") or "story location",
                time_of_day=default_tod,
                mood="engaged",
            )
            for h in scene_hints
        ] or [SceneSpec(scene_id="s1", location="story location", time_of_day=default_tod)]

        # Map timeline into scenes by equal split for heuristic
        lines = [ev for ev in timeline if ev["type"] == "line"]
        shots: list[ShotSpec] = []
        n_scenes = max(1, len(scenes))
        for i, ev in enumerate(lines):
            scene = scenes[min(i * n_scenes // max(len(lines), 1), n_scenes - 1)]
            hint = next((h for h in scene_hints if h["scene_id"] == scene.scene_id), {})
            colocated = [c.upper() for c in (hint.get("colocated_characters") or [])]
            speaker = (ev.get("speaker") or "").upper()
            remote = bool(hint.get("remote_dialogue"))

            if i == 0 or (i > 0 and scene.scene_id != shots[-1].scene_id if shots else True):
                size, on_screen = "establishing_wide", []
            elif not remote and len(colocated) >= 3 and i % 4 == 1:
                size, on_screen = "group", colocated[:4]
            elif not remote and len(colocated) >= 2 and i % 3 == 1:
                size, on_screen = "two_shot", colocated[:2]
            elif not remote and len(colocated) >= 2 and i % 3 == 2:
                size = "ots"
                on_screen = ([speaker] + [c for c in colocated if c != speaker])[:2]
            elif speaker in {c.id for c in characters}:
                size, on_screen = "medium", [speaker]
            else:
                size, on_screen = "wide", []

            shots.append(
                ShotSpec(
                    shot_id=f"sh{i + 1:02d}",
                    scene_id=scene.scene_id,
                    t_start=ev["t_start"],
                    t_end=ev["t_end"],
                    shot_size=size,
                    characters_on_screen=on_screen,
                    action="Scene matching the narration beat.",
                    camera_motion=("slow_push_in", "static", "pan_right", "slow_pull_out")[i % 4],
                    seq_ids=[ev["seq_id"]],
                )
            )
        shots = _snap_shots(shots, duration)
        style_fields = {
            k: v for k, v in guide.items() if k in StyleSpec.model_fields and v
        }
        plan = EpisodeVisualPlan(
            series_id=series_id,
            title=package.get("title"),
            language=package.get("language") or "hi",
            style=StyleSpec(**style_fields),
            characters=characters,
            scenes=scenes,
            shots=shots,
        )
        _repair_multi_character_coverage(plan, scene_hints)
        log.info("director_heuristic shots=%d", len(plan.shots))
        return plan
