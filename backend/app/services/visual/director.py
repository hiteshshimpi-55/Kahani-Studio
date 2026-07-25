"""Visual Director — script + timings → VisualTrack shot list (no GPU)."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.integrations.databricks.vector_search import VectorSearchQuery, similarity_search
from app.schemas.visual.track import (
    AspectRatio,
    CameraAngle,
    CameraLevel,
    CameraMovement,
    CharacterIdentitySheet,
    CharacterOnScreen,
    DensityMode,
    Framing,
    LocationSheet,
    MediaKind,
    ShotSize,
    StyleBible,
    VisualDirectorInput,
    VisualShot,
    VisualTrack,
)

log = logging.getLogger(__name__)

HIGH_EMOTION = {
    "fear",
    "terror",
    "panic",
    "gasp",
    "scream",
    "rage",
    "shock",
    "whisper_threat",
    "menace",
    "suppressed_anger",
    "terrified",
    "panicked",
}

DENSITY_INTERVAL = {
    DensityMode.SPARSE: 35.0,
    DensityMode.NORMAL: 25.0,
    DensityMode.DENSE: 15.0,
}


def _as_dict(beat: Any) -> dict[str, Any]:
    if isinstance(beat, dict):
        return beat
    if hasattr(beat, "model_dump"):
        return beat.model_dump()
    return dict(beat)


def _emotion(beat: dict[str, Any]) -> str:
    return str(beat.get("emotion") or beat.get("mood") or "").lower()


def _speaker(beat: dict[str, Any]) -> str | None:
    return beat.get("speaker") or beat.get("narrator_id") or beat.get("character_id")


def _location(beat: dict[str, Any]) -> str | None:
    return beat.get("location_id") or beat.get("location") or beat.get("setting")


def _beat_time(beat: dict[str, Any], seq_timings: dict[str, dict[str, float]], fallback: float) -> float:
    seq_ids = beat.get("seq_ids") or beat.get("source_beats") or []
    if isinstance(seq_ids, str):
        seq_ids = [seq_ids]
    for sid in seq_ids:
        t = seq_timings.get(str(sid))
        if t and "t_start" in t:
            return float(t["t_start"])
    if "t_start" in beat:
        return float(beat["t_start"])
    if "t_start_hint" in beat:
        return float(beat["t_start_hint"])
    return fallback


def _beat_end(beat: dict[str, Any], seq_timings: dict[str, dict[str, float]], start: float) -> float:
    seq_ids = beat.get("seq_ids") or beat.get("source_beats") or []
    if isinstance(seq_ids, str):
        seq_ids = [seq_ids]
    ends = []
    for sid in seq_ids:
        t = seq_timings.get(str(sid))
        if t and "t_end" in t:
            ends.append(float(t["t_end"]))
    if ends:
        return max(ends)
    if "t_end" in beat:
        return float(beat["t_end"])
    return start + 8.0


def _search_shot_template(query: str) -> dict[str, Any] | None:
    try:
        result = similarity_search(
            VectorSearchQuery(
                query_text=query,
                columns=[
                    "id",
                    "asset_type",
                    "provider_id",
                    "name",
                    "description",
                    "tags",
                    "use_case",
                ],
                num_results=1,
                filters={"asset_type": "shot_template"},
                query_type="ANN",
                endpoint_name=settings.databricks_vector_search_endpoint,
                index_name=settings.databricks_cast_index_fqn,
            )
        )
        if result.hits:
            return dict(result.hits[0].raw)
    except Exception as exc:
        log.warning("shot_template_search_skipped err=%s", exc)
    return None


def _sheet_for(speaker: str | None, sheets: list[CharacterIdentitySheet]) -> CharacterIdentitySheet | None:
    if not speaker:
        return None
    key = speaker.upper()
    for s in sheets:
        if s.character_id.upper() == key or s.display_name.upper() == key:
            return s
    return None


def _map_expression(emotion: str) -> str:
    e = emotion.lower()
    if e in {"fear", "terror", "terrified"}:
        return "fear"
    if e in {"gasp", "shock", "panic", "panicked"}:
        return "gasp"
    if e in {"whisper", "nervous", "whispering"}:
        return "whisper"
    if e in {"dismissive", "amused"}:
        return "dismissive"
    if e in {"menace", "threat", "cold"}:
        return "menace"
    if e in {"anger", "rage", "suppressed_anger"}:
        return "anger"
    return "neutral"


class VisualDirectorService:
    """Heuristic Visual Director with optional shot_template vector priors."""

    def plan(self, inp: VisualDirectorInput) -> VisualTrack:
        style = inp.style_bible
        beats = [_as_dict(b) for b in inp.beats]
        if not beats and inp.narration_sequence:
            # Fall back: treat narration sequence as beats
            for i, seq in enumerate(inp.narration_sequence):
                s = _as_dict(seq)
                beats.append(
                    {
                        "beat_id": s.get("seq_id") or f"seq_{i}",
                        "seq_ids": [s.get("seq_id")] if s.get("seq_id") else [],
                        "type": s.get("kind") or "narration",
                        "speaker": s.get("speaker") or s.get("narrator_id"),
                        "emotion": s.get("emotion"),
                        "text": s.get("text"),
                        "location_id": s.get("location_id"),
                    }
                )

        interval = DENSITY_INTERVAL.get(style.density, 35.0)
        max_shots = style.max_stills_per_part
        shots: list[VisualShot] = []
        ledger = {
            "active_location": None,
            "on_screen": [],
            "mood": None,
            "last_t": 0.0,
        }

        # Always open with an establish if we have duration
        if inp.part_duration_sec > 0 and beats:
            first = beats[0]
            t0 = _beat_time(first, inp.seq_timings, 0.0)
            t1 = min(max(t0 + 10.0, _beat_end(first, inp.seq_timings, t0)), inp.part_duration_sec)
            shots.append(
                self._build_shot(
                    shot_id=f"p{inp.part}_sh01",
                    start=t0,
                    end=max(t1, t0 + 1.5),
                    beat=first,
                    trigger="establish",
                    sheets=inp.identity_sheets,
                    locations=inp.location_sheets,
                    style=style,
                    force_framing=Framing.SINGLE,
                    force_size=ShotSize.ELS,
                )
            )
            ledger["active_location"] = _location(first)
            ledger["last_t"] = shots[-1].t_end_sec

        for beat in beats:
            start = _beat_time(beat, inp.seq_timings, ledger["last_t"])
            end = _beat_end(beat, inp.seq_timings, start)
            end = max(end, start + 1.5)
            if end > inp.part_duration_sec > 0:
                end = inp.part_duration_sec

            trigger = self._detect_trigger(beat, ledger, start, interval)
            if not trigger:
                continue
            if len(shots) >= max_shots:
                break

            # Avoid tiny adjacent cuts
            if shots and start < shots[-1].t_end_sec - 0.5:
                start = shots[-1].t_end_sec
                if end <= start + 1.5:
                    end = start + 1.5

            shot = self._build_shot(
                shot_id=f"p{inp.part}_sh{len(shots)+1:02d}",
                start=start,
                end=end,
                beat=beat,
                trigger=trigger,
                sheets=inp.identity_sheets,
                locations=inp.location_sheets,
                style=style,
            )
            shots.append(shot)
            ledger["active_location"] = shot.location_id or ledger["active_location"]
            ledger["on_screen"] = [c.character_id for c in shot.characters]
            ledger["mood"] = shot.mood
            ledger["last_t"] = shot.t_end_sec

        return VisualTrack(
            series_id=inp.series_id,
            part=inp.part,
            density=style.density,
            aspect_ratio=style.aspect_ratio,
            shots=shots,
            identity_sheet_ids=[s.character_id for s in inp.identity_sheets],
            notes=f"planned_shots={len(shots)} density={style.density}",
        )

    def _detect_trigger(
        self,
        beat: dict[str, Any],
        ledger: dict[str, Any],
        start: float,
        interval: float,
    ) -> str | None:
        loc = _location(beat)
        if loc and loc != ledger.get("active_location"):
            return "location_change"
        emo = _emotion(beat)
        if emo and any(k in emo for k in HIGH_EMOTION):
            return "emotion_spike"
        btype = str(beat.get("type") or "").lower()
        if btype in {"reveal", "cliff", "supernatural"}:
            return "cliff_reveal"
        if btype == "dialogue":
            return "dialogue"
        speaker = _speaker(beat)
        if speaker and speaker not in (ledger.get("on_screen") or []):
            return "character_enter"
        if start - float(ledger.get("last_t") or 0) >= interval:
            return "time_budget"
        return None

    def _build_shot(
        self,
        *,
        shot_id: str,
        start: float,
        end: float,
        beat: dict[str, Any],
        trigger: str,
        sheets: list[CharacterIdentitySheet],
        locations: list[LocationSheet],
        style: StyleBible,
        force_framing: Framing | None = None,
        force_size: ShotSize | None = None,
    ) -> VisualShot:
        emo = _emotion(beat)
        speaker = _speaker(beat)
        loc = _location(beat) or (locations[0].location_id if locations else None)
        text = str(beat.get("text") or beat.get("visual_cues") or "")
        query = f"{trigger} {emo} {text} horror thriller cinematic still"
        tmpl = _search_shot_template(query)

        size = force_size or ShotSize.MS
        angle = CameraAngle.NEUTRAL
        level = CameraLevel.EYE
        framing = force_framing or Framing.SINGLE
        if tmpl:
            tags = str(tmpl.get("tags") or "")
            for s in ShotSize:
                if s.value in tags.split(","):
                    size = s
                    break
            for a in CameraAngle:
                if a.value in tags.split(","):
                    angle = a
                    break
            for lv in CameraLevel:
                if lv.value in tags.split(","):
                    level = lv
                    break
            use = str(tmpl.get("use_case") or "")
            for f in Framing:
                if f.value == use or f.value in tags:
                    framing = f
                    break

        elif trigger in {"character_enter", "dialogue", "location_change"}:
            # Waist-up is still too tight for Flux — prefer MLS so SET reads.
            size = ShotSize.MLS
            framing = Framing.TWO_SHOT if len(sheets) >= 2 else Framing.SINGLE
            angle = CameraAngle.NEUTRAL
        elif trigger == "establish":
            size = ShotSize.ELS
            framing = Framing.SINGLE
        elif trigger == "time_budget":
            size = ShotSize.MLS
            framing = Framing.SINGLE

        btype = str(beat.get("type") or "").lower()
        if btype == "dialogue" and trigger not in {"establish", "emotion_spike"}:
            size = ShotSize.MLS
            framing = Framing.TWO_SHOT if len(sheets) >= 2 else Framing.SINGLE

        if trigger == "emotion_spike":
            # Fear punch still needs SET — medium shot at stairs/door, not headshot.
            size = ShotSize.MS
            framing = Framing.SINGLE
            angle = CameraAngle.LOW
        elif trigger == "cliff_reveal":
            size = ShotSize.MS
            angle = CameraAngle.DUTCH
            framing = Framing.SINGLE

        characters: list[CharacterOnScreen] = []
        sheet = _sheet_for(speaker, sheets)
        role_hint = str(beat.get("role") or beat.get("kind") or "")
        want_people = trigger != "establish" and "narrat" not in role_hint.lower()

        if want_people and sheet:
            # Dialogue / porch scenes: show speaking character + partner as two-shot.
            primary_pos = "left" if framing == Framing.TWO_SHOT else "center"
            characters.append(
                CharacterOnScreen(
                    character_id=sheet.character_id,
                    expression=_map_expression(emo),
                    pose=_pose_for(trigger, btype, emo),
                    screen_position=primary_pos,
                    facing="three_quarter" if framing == Framing.TWO_SHOT else "camera",
                    identity_sheet_id=sheet.character_id,
                    face_ref_url=(
                        (sheet.turnaround_urls or {}).get("front")
                        or next(iter((sheet.turnaround_urls or {}).values()), None)
                    ),
                )
            )
            if framing in {Framing.TWO_SHOT, Framing.OTS, Framing.GROUP} or trigger in {
                "character_enter",
                "dialogue",
            }:
                for other in sheets:
                    if other.character_id == sheet.character_id:
                        continue
                    if len(characters) >= style.max_on_screen_characters:
                        break
                    characters.append(
                        CharacterOnScreen(
                            character_id=other.character_id,
                            expression="dismissive" if "dismiss" in emo else "neutral",
                            pose="standing opposite, listening",
                            screen_position="right",
                            facing="three_quarter",
                            identity_sheet_id=other.character_id,
                            face_ref_url=(
                                (other.turnaround_urls or {}).get("front")
                                or next(iter((other.turnaround_urls or {}).values()), None)
                            ),
                        )
                    )
                    framing = Framing.TWO_SHOT
                    if size in {ShotSize.ECU, ShotSize.CU}:
                        size = ShotSize.MS
                    break

        # Build cinematic director intent from the script line, not "emotion_spike: …"
        intent = _cinematic_intent(
            trigger=trigger,
            text=text,
            emo=emo,
            framing=framing,
            size=size,
            speaker=sheet.display_name if sheet else speaker,
            characters=characters,
            sheets=sheets,
        )
        if tmpl and tmpl.get("name"):
            intent = f"{intent} | template={tmpl.get('name')}"

        return VisualShot(
            shot_id=shot_id,
            beat_ids=[str(beat.get("beat_id") or "")] if beat.get("beat_id") else [],
            seq_ids=[str(x) for x in (beat.get("seq_ids") or beat.get("source_beats") or []) if x],
            t_start_sec=float(start),
            t_end_sec=float(end),
            media_kind=MediaKind.STILL,
            shot_size=size,
            camera_angle=angle,
            camera_level=level,
            camera_movement=CameraMovement.STATIC,
            framing=framing,
            characters=characters,
            location_id=loc,
            time_of_day=str(beat.get("time_of_day") or "night"),
            weather=beat.get("weather"),
            lighting=beat.get("lighting") or "moody practical porch light, deep shadows",
            mood=emo or (tmpl or {}).get("mood") or "uneasy",
            visual_intent=intent,
            aspect_ratio=style.aspect_ratio or AspectRatio.PORTRAIT,
            trigger_reason=trigger,
        )


def _pose_for(trigger: str, btype: str, emo: str) -> str:
    if btype == "dialogue" or trigger == "dialogue":
        return "standing at doorway arguing, half-body visible"
    if trigger == "emotion_spike" or "fear" in emo:
        return "recoiling near open door, looking upstairs, torso in frame"
    if trigger == "cliff_reveal":
        return "frozen mid-step inside dark house doorway"
    return "full upper body in scene, standing in environment"


def _cinematic_intent(
    *,
    trigger: str,
    text: str,
    emo: str,
    framing: Framing,
    size: ShotSize,
    speaker: str | None,
    characters: list[CharacterOnScreen],
    sheets: list[CharacterIdentitySheet],
) -> str:
    names = []
    for ch in characters:
        for s in sheets:
            if s.character_id == ch.character_id:
                names.append(s.display_name)
                break
        else:
            names.append(ch.character_id)
    cast = " and ".join(names) if names else "no characters on screen"
    line = text[:180] if text else ""
    if trigger == "establish":
        return (
            f"Cinematic establishing film still of the location at night. "
            f"Empty frame, no people. Atmosphere only. Line: {line}"
        )
    if framing == Framing.TWO_SHOT or len(characters) >= 2:
        return (
            f"Wide cinematic {size.value} two-shot of {cast} on the porch of an abandoned "
            f"night house. FULL bodies or knee-up, open door and porch light clearly visible, "
            f"foggy night. Characters facing each other mid-conversation, gesturing. "
            f"Camera pulled back — environment is 60% of frame. Dialogue ({emo}): \"{line}\". "
            f"NOT a face close-up."
        )
    return (
        f"Cinematic {size.value} of {speaker or cast} inside/at the abandoned house. "
        f"Show doorway, stairs, porch architecture. Character knee-up or waist-up max. "
        f"Beat ({emo}): \"{line}\". NOT a headshot."
    )
