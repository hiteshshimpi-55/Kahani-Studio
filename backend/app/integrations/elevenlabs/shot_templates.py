"""Curated cinematic shot templates for vector search (not movie pixels).

These encode Camera Artist / CineScale / Visibl-style language as searchable text
rows. We do NOT ingest CineScale/MovieNet frames — only enums + prompt priors.
"""

from __future__ import annotations

from datetime import datetime, timezone

SHOT_TEMPLATES: list[dict] = [
    {
        "slug": "horror_establish_house_night",
        "name": "Horror establish abandoned house night",
        "shot_size": "els",
        "camera_angle": "neutral",
        "camera_level": "eye",
        "framing": "single",
        "mood": "uneasy",
        "when": "Open part / location change to exterior night house",
        "description": (
            "Extreme long shot establishing an abandoned house at night. "
            "Neutral eye-level camera, sparse lighting, wind, dread. "
            "Horror thriller Pocket FM companion still. No faces required."
        ),
    },
    {
        "slug": "horror_doorway_two_shot_argue",
        "name": "Horror doorway two-shot argue",
        "shot_size": "ms",
        "camera_angle": "neutral",
        "camera_level": "eye",
        "framing": "two_shot",
        "mood": "tension",
        "when": "Two characters argue at a door — nervous vs dismissive",
        "description": (
            "Medium two-shot at an old doorway at night. Left nervous young woman, "
            "right dismissive young man. Eye-level, static. Horror serial dialogue beat."
        ),
    },
    {
        "slug": "horror_ecu_gasp_fear",
        "name": "Horror ECU gasp fear",
        "shot_size": "ecu",
        "camera_angle": "low",
        "camera_level": "eye",
        "framing": "single",
        "mood": "panic",
        "when": "Emotion spike — gasp, panic, whispered name reveal",
        "description": (
            "Extreme close-up of terrified face gasping. Slight low angle for menace. "
            "Horror emotion spike still. Same identity face, fear expression."
        ),
    },
    {
        "slug": "horror_dutch_entity_whisper",
        "name": "Horror dutch entity whisper",
        "shot_size": "mcu",
        "camera_angle": "dutch",
        "camera_level": "shoulder",
        "framing": "single",
        "mood": "supernatural",
        "when": "Supernatural voice / entity reveal",
        "description": (
            "Dutch angle medium close-up of a shadowy supernatural presence whispering. "
            "Distorted, menacing, horror entity. Prefer silhouette over clear face."
        ),
    },
    {
        "slug": "horror_insert_door_ajar",
        "name": "Horror insert door ajar",
        "shot_size": "cu",
        "camera_angle": "high",
        "camera_level": "shoulder",
        "framing": "insert",
        "mood": "dread",
        "when": "Prop/detail beat — door already open",
        "description": (
            "Insert close-up of a heavy wooden door cracked open in darkness. "
            "No people. Horror detail / foreshadowing still."
        ),
    },
    {
        "slug": "horror_ots_scared_to_friend",
        "name": "Horror OTS scared to friend",
        "shot_size": "ms",
        "camera_angle": "neutral",
        "camera_level": "eye",
        "framing": "over_the_shoulder",
        "mood": "uneasy",
        "when": "Dialogue reaction across two characters",
        "description": (
            "Over-the-shoulder medium shot from dismissive friend toward scared woman. "
            "Horror dialogue reaction framing."
        ),
    },
    {
        "slug": "thriller_corridor_whisper_echo",
        "name": "Thriller corridor whisper echo",
        "shot_size": "ls",
        "camera_angle": "neutral",
        "camera_level": "eye",
        "framing": "single",
        "mood": "eerie",
        "when": "Interior hall / upstairs call",
        "description": (
            "Long shot down an empty dark corridor with soft whisper atmosphere. "
            "Thriller/horror interior establish."
        ),
    },
    {
        "slug": "romance_intimate_two_shot",
        "name": "Romance intimate two-shot",
        "shot_size": "mcu",
        "camera_angle": "neutral",
        "camera_level": "eye",
        "framing": "two_shot",
        "mood": "warm",
        "when": "Soft dialogue intimacy",
        "description": (
            "Intimate medium close-up two-shot, warm key light, soft romance serial mood."
        ),
    },
    {
        "slug": "narration_wide_city_night",
        "name": "Narration wide city night",
        "shot_size": "els",
        "camera_angle": "high",
        "camera_level": "aerial",
        "framing": "single",
        "mood": "melancholy",
        "when": "Narrator sets place without characters on screen",
        "description": (
            "Wide aerial/high establishing city or outskirts at night under narrator VO. "
            "No faces. Melancholy thriller atmosphere."
        ),
    },
    {
        "slug": "action_push_in_threat",
        "name": "Action push-in threat",
        "shot_size": "ms",
        "camera_angle": "low",
        "camera_level": "hip",
        "framing": "single",
        "mood": "threat",
        "when": "Threat escalation / antagonist presence",
        "description": (
            "Low-angle medium shot with implied push-in on a threatening figure. "
            "Thriller antagonist energy."
        ),
    },
    {
        "slug": "group_three_outside_house",
        "name": "Group three outside house",
        "shot_size": "mls",
        "camera_angle": "neutral",
        "camera_level": "eye",
        "framing": "group",
        "mood": "uneasy",
        "when": "Three friends arrive at location",
        "description": (
            "Medium-long group shot of three friends outside an old house at night. "
            "Horror arrival beat, eye-level static."
        ),
    },
    {
        "slug": "pov_looking_upstairs",
        "name": "POV looking upstairs",
        "shot_size": "ms",
        "camera_angle": "low",
        "camera_level": "eye",
        "framing": "pov",
        "mood": "dread",
        "when": "Character looks toward upstairs voice",
        "description": (
            "POV shot looking up a dark stairwell toward an unseen voice. "
            "Horror dread, low angle."
        ),
    },
]


def curated_shot_template_rows() -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict] = []
    for e in SHOT_TEMPLATES:
        description = (
            f"Shot template: {e['name']}. "
            f"Shot size: {e['shot_size']}. Angle: {e['camera_angle']}. "
            f"Level: {e['camera_level']}. Framing: {e['framing']}. Mood: {e['mood']}. "
            f"When to use: {e['when']}. {e['description']} "
            "Cinematic companion still for audiobook VisualTrack planning."
        )
        rows.append(
            {
                "id": f"shot_{e['slug']}",
                "asset_type": "shot_template",
                "provider": "kissa",
                "provider_id": e["slug"],
                "name": e["name"],
                "language": "any",
                "gender": None,
                "age": None,
                "accent": None,
                "use_case": e["framing"],
                "free_users_allowed": True,
                "preview_url": None,
                "tags": (
                    f"{e['shot_size']},{e['camera_angle']},{e['camera_level']},"
                    f"{e['framing']},{e['mood']},shot_template"
                ),
                "description": description,
                "updated_at": now,
            }
        )
    return rows
