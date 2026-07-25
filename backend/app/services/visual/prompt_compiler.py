"""Compile VisualShot + style/identity into cinematic scene prompts."""

from __future__ import annotations

from app.schemas.visual.track import (
    CharacterIdentitySheet,
    Framing,
    LocationSheet,
    ShotSize,
    StyleBible,
    VisualShot,
)

_SIZE_WORDS = {
    ShotSize.ECU: "tight emotional close-up with background still visible",
    ShotSize.CU: "close-up shoulders-and-up inside the location",
    ShotSize.MCU: "medium close-up chest-up, location readable behind subject",
    ShotSize.MS: "medium shot waist-up, clear environment",
    ShotSize.MLS: "medium-long shot full body in environment",
    ShotSize.LS: "long shot characters small in frame",
    ShotSize.ELS: "extreme long establishing shot of location only",
}

_DEFAULT_NEGATIVE = (
    "studio portrait, headshot, passport photo, beauty close-up, "
    "zoomed face filling frame, plain backdrop, white background, "
    "instagram selfie, face only, cropped above shoulders only, "
    "bad quality, worst quality, text, signature, watermark, logo, "
    "extra limbs, deformed eyes, blurry, low resolution"
)


def _is_wide_scene(shot: VisualShot) -> bool:
    return shot.shot_size in {
        ShotSize.MS,
        ShotSize.MLS,
        ShotSize.LS,
        ShotSize.ELS,
    } or shot.framing in {Framing.TWO_SHOT, Framing.GROUP, Framing.OTS, Framing.INSERT}


def compile_shot_prompt(
    shot: VisualShot,
    *,
    style: StyleBible,
    identity_sheets: list[CharacterIdentitySheet] | None = None,
    location_sheets: list[LocationSheet] | None = None,
) -> tuple[str, str]:
    """Return (compiled_prompt, negative_prompt) biased toward film stills, not portraits."""
    sheets_by_id = {s.character_id: s for s in (identity_sheets or [])}
    sheets_by_name = {s.display_name.upper(): s for s in (identity_sheets or [])}
    locs = {loc.location_id: loc for loc in (location_sheets or [])}

    parts: list[str] = [
        "Cinematic film production still from a horror thriller serial",
        "vertical 9:16 companion image for an audiobook scene",
        _SIZE_WORDS.get(shot.shot_size, "cinematic still"),
        f"{shot.camera_angle.value} camera angle",
        f"{shot.camera_level.value}-level",
        f"{shot.framing.value.replace('_', ' ')} framing",
        "anamorhic film look, teal-orange grade, practical night lighting",
    ]

    # Location FIRST — scenes live in places, not face zooms.
    if shot.location_id and shot.location_id in locs:
        loc = locs[shot.location_id]
        parts.append(
            f"PRIMARY SET: {loc.name}. {loc.description}. "
            "Architecture and atmosphere must dominate the frame"
        )
    elif shot.location_id:
        parts.append(f"PRIMARY SET: {shot.location_id}")

    if shot.time_of_day:
        parts.append(f"time: {shot.time_of_day}")
    if shot.weather:
        parts.append(f"weather: {shot.weather}")
    if shot.lighting:
        parts.append(f"lighting: {shot.lighting}")
    if shot.mood:
        parts.append(f"mood: {shot.mood}")

    if shot.framing == Framing.INSERT or not shot.characters:
        parts.append("empty set, no people, no readable faces, environment only")
    else:
        # Blocking before identity tokens
        if shot.framing == Framing.TWO_SHOT or len(shot.characters) >= 2:
            parts.append(
                "TWO CHARACTERS in conversation, both fully visible in frame, "
                "standing opposite each other at the doorway/porch, "
                "body language readable, not cropped to faces"
            )
        for ch in shot.characters:
            sheet = sheets_by_id.get(ch.character_id) or sheets_by_name.get(
                ch.character_id.upper()
            )
            name = sheet.display_name if sheet else ch.character_id
            tokens = sheet.identity_tokens if sheet else ""
            pose = ch.pose or "standing in the scene"
            pos = ch.screen_position or "center"
            facing = ch.facing or "three_quarter"
            # Keep identity short so location wins the prompt
            short_tokens = ", ".join(tokens.split(",")[:4]) if tokens else name
            parts.append(
                f"{name} on {pos} ({short_tokens}), expression {ch.expression}, "
                f"pose: {pose}, facing {facing}"
            )

    parts.append(f"DIRECTOR INTENT: {shot.visual_intent}")
    parts.append(f"style bible: {style.look}")
    if _is_wide_scene(shot):
        parts.append(
            "IMPORTANT: show the SET and BODY LANGUAGE. "
            "Do not generate a face-only portrait. Characters mid-frame in the location."
        )
    else:
        parts.append(
            "Keep background context visible; avoid studio headshot aesthetic"
        )

    prompt = ". ".join(p.strip().rstrip(".") for p in parts if p) + "."
    avoid = list(style.avoid or [])
    negative = _DEFAULT_NEGATIVE
    if avoid:
        negative = f"{negative}, {', '.join(avoid)}"
    if shot.negative_prompt:
        negative = f"{negative}, {shot.negative_prompt}"
    if _is_wide_scene(shot):
        negative = (
            f"{negative}, extreme close-up, macro face, beauty dish portrait, "
            "centered passport crop"
        )
    return prompt, negative


def should_use_face_lock(shot: VisualShot) -> bool:
    """PuLID only for intentional single CU/ECU punches — scenes use Flux."""
    if not shot.characters:
        return False
    if shot.framing != Framing.SINGLE:
        return False
    return shot.shot_size in {ShotSize.CU, ShotSize.ECU}
