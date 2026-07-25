"""Curated visual shot-grammar catalog for the Director agent.

Same pattern as SFX: searchable templates (asset_type=shot_template) that the
director retrieves per beat, then adapts to the specific story. Covers Pocket
FM / Kuku TV–style vertical drama coverage — establishing, dialogue OTS /
two-shot, group reveals, forensic, phone, travel, inserts, reactions.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Each entry is a reusable coverage pattern the director must pick from /
# adapt — not a finished image prompt.
SHOT_TEMPLATES: list[dict] = [
    # ── Establishing / geography ────────────────────────────────────
    {
        "slug": "est_bedroom_night_rain",
        "name": "Night bedroom establishing (rain)",
        "shot_size": "establishing_wide",
        "camera_motion": "static",
        "min_chars": 0,
        "max_chars": 1,
        "tags": "establishing,bedroom,night,rain,interior,lonely",
        "when": "Open a late-night bedroom / apartment scene. Geography first.",
        "composition": "Wide of room; character tiny or absent; rain on window; practical lamp optional.",
    },
    {
        "slug": "est_forensic_lab",
        "name": "Forensic lab establishing",
        "shot_size": "establishing_wide",
        "camera_motion": "slow_pull_out",
        "min_chars": 0,
        "max_chars": 0,
        "tags": "establishing,lab,forensic,hospital,clinical,sterile,interior",
        "when": "Arrive at forensic / hospital / lab location before dialogue.",
        "composition": "Long corridor or wide lab; fluorescent harsh light; stainless steel; no people yet.",
    },
    {
        "slug": "est_rain_street_night",
        "name": "Rain-slicked night street establishing",
        "shot_size": "establishing_wide",
        "camera_motion": "pan_right",
        "min_chars": 0,
        "max_chars": 1,
        "tags": "establishing,street,rain,night,mumbai,city,travel",
        "when": "City travel / urgency beat between locations at night.",
        "composition": "Wet asphalt, neon reflections, sparse traffic; vehicle optional and small.",
    },
    {
        "slug": "est_police_station",
        "name": "Police station / interrogation room establishing",
        "shot_size": "establishing_wide",
        "camera_motion": "static",
        "min_chars": 0,
        "max_chars": 2,
        "tags": "establishing,police,station,interrogation,interior,procedural",
        "when": "Enter a police station, interrogation room, or office.",
        "composition": "Wide of institutional room; fluorescent; desk/chairs; characters small if present.",
    },
    # ── Phone / remote dialogue (singles OK) ────────────────────────
    {
        "slug": "phone_mcu_speaker",
        "name": "Phone call MCU of speaker",
        "shot_size": "medium",
        "camera_motion": "static",
        "min_chars": 1,
        "max_chars": 1,
        "tags": "phone,call,dialogue,remote,single,mcu,night",
        "when": "Character on phone alone — remote conversation, not co-located.",
        "composition": "Chest-up single holding phone; face lit by screen or lamp; other party OFF frame.",
    },
    {
        "slug": "phone_cu_reaction",
        "name": "Phone call reaction close-up",
        "shot_size": "close_up",
        "camera_motion": "slow_push_in",
        "min_chars": 1,
        "max_chars": 1,
        "tags": "phone,reaction,closeup,shock,single,remote",
        "when": "Shocking news arrives over the phone — show the LISTENER's face.",
        "composition": "Tight face; eyes widen; phone at ear; no second person in room.",
    },
    {
        "slug": "insert_phone_vibrate",
        "name": "Insert ringing / vibrating phone",
        "shot_size": "insert",
        "camera_motion": "static",
        "min_chars": 0,
        "max_chars": 0,
        "tags": "insert,phone,sfx,object,night,bedside",
        "when": "SFX phone ring / vibrate beat.",
        "composition": "Detail of phone on table/bed vibrating; shallow focus.",
    },
    # ── Two-person co-located dialogue (MUST use these) ─────────────
    {
        "slug": "two_shot_dialogue",
        "name": "Two-shot dialogue master",
        "shot_size": "two_shot",
        "camera_motion": "static",
        "min_chars": 2,
        "max_chars": 2,
        "tags": "dialogue,two_shot,colocated,conversation,relationship",
        "when": "Two named characters are in the SAME physical location talking.",
        "composition": "Both waist-up in one frame; clear spatial relationship; eye lines match 180° rule.",
    },
    {
        "slug": "ots_speaker_a",
        "name": "Over-the-shoulder of speaker A",
        "shot_size": "ots",
        "camera_motion": "static",
        "min_chars": 2,
        "max_chars": 2,
        "tags": "dialogue,ots,over_shoulder,colocated,speaker",
        "when": "Co-located dialogue — cover the speaker past the listener's shoulder.",
        "composition": "Foreground shoulder/back of listener; speaker face clear; matched framing for reverse.",
    },
    {
        "slug": "ots_speaker_b",
        "name": "Over-the-shoulder of speaker B (reverse)",
        "shot_size": "ots",
        "camera_motion": "static",
        "min_chars": 2,
        "max_chars": 2,
        "tags": "dialogue,ots,over_shoulder,colocated,reverse",
        "when": "Reverse OTS when the other character speaks in the same room.",
        "composition": "Matched reverse of ots_speaker_a; keep 180° line.",
    },
    {
        "slug": "two_shot_tense_reveal",
        "name": "Tense two-shot on revelation",
        "shot_size": "two_shot",
        "camera_motion": "slow_push_in",
        "min_chars": 2,
        "max_chars": 2,
        "tags": "dialogue,two_shot,reveal,tension,colocated,thriller",
        "when": "Big reveal shared between two people in the same room.",
        "composition": "Both faces readable; one delivers news, other reacts — both ON screen.",
    },
    {
        "slug": "confrontation_two_shot",
        "name": "Confrontation / interrogation two-shot",
        "shot_size": "two_shot",
        "camera_motion": "static",
        "min_chars": 2,
        "max_chars": 2,
        "tags": "interrogation,confrontation,police,two_shot,colocated",
        "when": "Police questioning, accusation, or standoff between two characters.",
        "composition": "Facing each other across desk/table; power distance visible in blocking.",
    },
    # ── Group / 3+ characters ───────────────────────────────────────
    {
        "slug": "group_evidence_table",
        "name": "Group around evidence table",
        "shot_size": "group",
        "camera_motion": "static",
        "min_chars": 3,
        "max_chars": 5,
        "tags": "group,evidence,lab,police,forensic,reveal,colocated,body",
        "when": "Doctor/forensic expert presents findings to one or more police officers.",
        "composition": "ALL named people ON screen around table/tray; evidence/body visible mid-frame; doctor gesturing.",
    },
    {
        "slug": "group_lab_body_reveal",
        "name": "Lab: doctor shows body/findings to police",
        "shot_size": "group",
        "camera_motion": "slow_push_in",
        "min_chars": 2,
        "max_chars": 4,
        "tags": "group,lab,body,autopsy,forensic,police,doctor,reveal,colocated",
        "when": "Forensic reveal — poison, wounds, autopsy finding. Doctor + police MUST share frame with body/evidence.",
        "composition": "Doctor pointing at body/wound/chart; inspector + junior officer looking; clinical light; no 'off-screen' people.",
    },
    {
        "slug": "group_briefing",
        "name": "Team briefing group shot",
        "shot_size": "group",
        "camera_motion": "static",
        "min_chars": 3,
        "max_chars": 6,
        "tags": "group,briefing,police,team,office,colocated",
        "when": "Multiple officers / allies planning next move in one room.",
        "composition": "Wide enough to see all faces; hierarchical blocking (senior centered or foreground).",
    },
    {
        "slug": "group_then_single",
        "name": "Group open then cut to speaker single",
        "shot_size": "group",
        "camera_motion": "static",
        "min_chars": 3,
        "max_chars": 5,
        "tags": "group,coverage,dialogue,colocated,master",
        "when": "Start 3+ person scene with GROUP master before cutting to singles.",
        "composition": "Master showing full spatial layout; then later shots may go MCU.",
    },
    # ── Forensic / evidence specifics ───────────────────────────────
    {
        "slug": "insert_evidence_tray",
        "name": "Insert evidence tray / ring / object",
        "shot_size": "insert",
        "camera_motion": "slow_push_in",
        "min_chars": 0,
        "max_chars": 0,
        "tags": "insert,evidence,ring,tray,object,lab,reveal",
        "when": "Key prop reveal (ring, report, weapon, photo) — after or between dialogue.",
        "composition": "Macro of object on metal tray; engraving readable if text; sterile surface.",
    },
    {
        "slug": "ots_doctor_to_police",
        "name": "OTS doctor explaining to inspector",
        "shot_size": "ots",
        "camera_motion": "static",
        "min_chars": 2,
        "max_chars": 2,
        "tags": "ots,lab,doctor,police,explanation,colocated,forensic",
        "when": "Doctor speaks clinical findings to inspector in the lab — both present.",
        "composition": "Past inspector's shoulder onto doctor's face; lab coat; charts/body in soft BG.",
    },
    {
        "slug": "ots_police_to_doctor",
        "name": "OTS inspector reacting to doctor",
        "shot_size": "ots",
        "camera_motion": "slow_push_in",
        "min_chars": 2,
        "max_chars": 2,
        "tags": "ots,lab,police,reaction,colocated,forensic",
        "when": "Inspector absorbs shocking lab finding — reverse of doctor OTS.",
        "composition": "Past doctor's shoulder onto inspector's grim face; matched framing.",
    },
    {
        "slug": "two_shot_lab_with_body",
        "name": "Two-shot at autopsy / body table",
        "shot_size": "two_shot",
        "camera_motion": "static",
        "min_chars": 2,
        "max_chars": 2,
        "tags": "two_shot,lab,body,autopsy,doctor,police,colocated",
        "when": "Doctor and one officer beside the body discussing cause of death.",
        "composition": "Body mid/foreground; both characters upper frame; clinical, respectful, not gory.",
    },
    # ── Travel / action between scenes ──────────────────────────────
    {
        "slug": "car_exterior_rain_night",
        "name": "Police car racing through rain",
        "shot_size": "wide",
        "camera_motion": "pan_right",
        "min_chars": 0,
        "max_chars": 2,
        "tags": "travel,car,rain,night,urgency,wide",
        "when": "Narration of rushing to a location in rain.",
        "composition": "Exterior of car on wet street; headlights; rain streaks; characters inside optional.",
    },
    {
        "slug": "pov_windshield_rain",
        "name": "POV windshield heavy rain",
        "shot_size": "medium",
        "camera_motion": "static",
        "min_chars": 0,
        "max_chars": 1,
        "tags": "pov,car,rain,windshield,travel,sfx",
        "when": "SFX / narration of rain on windshield during drive.",
        "composition": "Through windshield; wipers; blurred city lights; driver silhouette optional.",
    },
    {
        "slug": "insert_ignition_keys",
        "name": "Insert key into ignition",
        "shot_size": "insert",
        "camera_motion": "static",
        "min_chars": 0,
        "max_chars": 1,
        "tags": "insert,car,keys,sfx,urgency",
        "when": "Car start SFX / departure beat.",
        "composition": "Hand + key in ignition; dashboard raindrops; shallow DOF.",
    },
    # ── Emotional singles (use sparingly when co-located) ───────────
    {
        "slug": "mcu_emotional_single",
        "name": "Emotional medium close-up single",
        "shot_size": "medium",
        "camera_motion": "static",
        "min_chars": 1,
        "max_chars": 1,
        "tags": "single,mcu,emotion,dialogue,coverage",
        "when": "After a group/two-shot master is already established — isolate speaker emotion.",
        "composition": "Chest-up; eyes clear; only AFTER multi-character geography is set.",
    },
    {
        "slug": "cu_revelation",
        "name": "Close-up on revelation / decision",
        "shot_size": "close_up",
        "camera_motion": "slow_push_in",
        "min_chars": 1,
        "max_chars": 1,
        "tags": "closeup,reveal,decision,emotion,thriller",
        "when": "Biggest emotional beat of a scene — one character's face only.",
        "composition": "Face fills frame; micro-expression; reserve for climax lines.",
    },
    {
        "slug": "ecu_eyes_or_object",
        "name": "Extreme close-up eyes or key object",
        "shot_size": "extreme_close_up",
        "camera_motion": "slow_push_in",
        "min_chars": 0,
        "max_chars": 1,
        "tags": "ecu,eyes,object,climax,once_per_episode",
        "when": "Episode climax only — once max.",
        "composition": "Eyes OR engraved object filling frame; maximum intensity.",
    },
    {
        "slug": "reaction_listener",
        "name": "Reaction shot of listener",
        "shot_size": "close_up",
        "camera_motion": "static",
        "min_chars": 1,
        "max_chars": 1,
        "tags": "reaction,listener,dialogue,colocated,after_shock",
        "when": "Right after a shocking line — cut to the person HEARING it, not the speaker.",
        "composition": "Listener face only; still in same location as speaker.",
    },
    # ── Romance / drama (generic for other scripts) ─────────────────
    {
        "slug": "two_shot_romance_soft",
        "name": "Soft two-shot romantic",
        "shot_size": "two_shot",
        "camera_motion": "slow_push_in",
        "min_chars": 2,
        "max_chars": 2,
        "tags": "romance,two_shot,intimacy,colocated,warm",
        "when": "Two characters sharing intimate dialogue in same space.",
        "composition": "Closer proximity; warm practical light; both faces soft.",
    },
    {
        "slug": "est_village_day",
        "name": "Village / outdoor day establishing",
        "shot_size": "establishing_wide",
        "camera_motion": "pan_left",
        "min_chars": 0,
        "max_chars": 2,
        "tags": "establishing,village,day,outdoor,india,historical",
        "when": "Open a rural / outdoor daytime scene.",
        "composition": "Wide landscape; dusty road or fields; people small.",
    },
    {
        "slug": "est_courtroom",
        "name": "Courtroom establishing",
        "shot_size": "establishing_wide",
        "camera_motion": "static",
        "min_chars": 0,
        "max_chars": 4,
        "tags": "establishing,court,legal,interior,drama",
        "when": "Enter a courtroom scene.",
        "composition": "Wide of bench, gallery, flags; characters small.",
    },
    {
        "slug": "group_court_argument",
        "name": "Courtroom group / lawyers + judge",
        "shot_size": "group",
        "camera_motion": "static",
        "min_chars": 3,
        "max_chars": 6,
        "tags": "group,court,argument,legal,colocated",
        "when": "Argument involving multiple parties in court.",
        "composition": "Judge elevated; lawyers standing; accused visible.",
    },
    {
        "slug": "horror_wide_empty",
        "name": "Horror empty space wide",
        "shot_size": "wide",
        "camera_motion": "slow_push_in",
        "min_chars": 0,
        "max_chars": 1,
        "tags": "horror,wide,empty,tension,atmosphere",
        "when": "Build dread with empty geography before a scare.",
        "composition": "Negative space dominates; one figure tiny or absent.",
    },
    {
        "slug": "insert_document_report",
        "name": "Insert document / postmortem report",
        "shot_size": "insert",
        "camera_motion": "static",
        "min_chars": 0,
        "max_chars": 1,
        "tags": "insert,document,report,paper,lab,police",
        "when": "Narration about a report, file, or written evidence.",
        "composition": "Hands holding stamped report; readable header; shallow focus.",
    },
]


def curated_shot_template_rows() -> list[dict]:
    """Rows for cast_assets / vector index (asset_type=shot_template)."""
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict] = []
    for e in SHOT_TEMPLATES:
        description = (
            f"Visual shot template: {e['name']}. "
            f"Shot size: {e['shot_size']}. Camera motion: {e['camera_motion']}. "
            f"Characters on screen: {e['min_chars']}-{e['max_chars']}. "
            f"When to use: {e['when']} "
            f"Composition rule: {e['composition']} "
            f"Tags: {e['tags']}. "
            "For Pocket FM / Kuku TV style vertical audio-drama companion visuals. "
            "Director agent retrieves this template and adapts action/wardrobe to the story beat. "
            "Prefer multi-character templates (two_shot, ots, group) whenever characters are co-located."
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
                "use_case": e["shot_size"],
                "free_users_allowed": True,
                "preview_url": None,
                "tags": (
                    f"{e['tags']},shot_template,{e['shot_size']},"
                    f"motion:{e['camera_motion']}|min_chars:{e['min_chars']}|max_chars:{e['max_chars']}"
                ),
                "description": description,
                "updated_at": now,
            }
        )
    return rows


def local_template_search(query: str, *, num_results: int = 6) -> list[dict]:
    """Keyword fallback when vector search is unavailable."""
    tokens = {t.lower() for t in query.replace(",", " ").split() if len(t) > 2}
    scored: list[tuple[float, dict]] = []
    for e in SHOT_TEMPLATES:
        hay = f"{e['name']} {e['tags']} {e['when']} {e['composition']} {e['shot_size']}".lower()
        score = sum(1.0 for t in tokens if t in hay)
        # Boost multi-character templates when query implies co-location
        colocated_hints = {"lab", "together", "group", "both", "doctor", "police", "dialogue", "colocated", "forensic", "body"}
        if tokens & colocated_hints and e["min_chars"] >= 2:
            score += 2.5
        if score > 0:
            scored.append((score, e))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:num_results]] or SHOT_TEMPLATES[:num_results]
