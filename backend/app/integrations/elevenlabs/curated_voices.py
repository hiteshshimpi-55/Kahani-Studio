"""Curated free-safe ElevenLabs voice seed (works without live API pull)."""

from __future__ import annotations

from datetime import datetime, timezone

# Premade / well-known library IDs commonly used in docs + demos.
# Descriptions are written for semantic casting (Hindi/EN serial audio).
CURATED_VOICES: list[dict] = [
    {
        "provider_id": "JBFqnCBsd6RMkjVDRZzb",
        "name": "George",
        "language": "en",
        "gender": "male",
        "age": "middle_aged",
        "accent": "british",
        "use_case": "narration",
        "asset_type": "narrator_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "narration,thriller,calm,measured,english",
        "blurb": (
            "Warm British male narrator with calm measured delivery. "
            "Excellent for mystery thriller storytelling, Pocket FM style serial narration, "
            "documentary tone, and horror framing. Steady pacing, authoritative but soft."
        ),
    },
    {
        "provider_id": "21m00Tcm4TlvDq8ikWAM",
        "name": "Rachel",
        "language": "en",
        "gender": "female",
        "age": "young",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "narrator_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "narration,female,young,american,calm",
        "blurb": (
            "Young American female narrator, soft and friendly yet clear. "
            "Good for romance-adjacent narration, intimate thriller POV, "
            "and calm storytelling with emotional range."
        ),
    },
    {
        "provider_id": "AZnzlk1XvdvUeBnXmlld",
        "name": "Domi",
        "language": "en",
        "gender": "female",
        "age": "young",
        "accent": "american",
        "use_case": "characters_animation",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "dialogue,female,young,strong,character",
        "blurb": (
            "Strong young female character voice with presence. "
            "Fits protagonists who are bold, tense, or confrontational in drama and thriller dialogue."
        ),
    },
    {
        "provider_id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Bella",
        "language": "en",
        "gender": "female",
        "age": "young",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "soft,female,young,whisper,emotional",
        "blurb": (
            "Soft young female voice suited to whispered fear, emotional beats, "
            "and intimate horror dialogue. Good for terrified or vulnerable characters."
        ),
    },
    {
        "provider_id": "ErXwobaYiN019PkySvjV",
        "name": "Antoni",
        "language": "en",
        "gender": "male",
        "age": "young",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,young,dialogue,warm",
        "blurb": (
            "Warm young male character voice for supportive or conflicted roles. "
            "Natural conversational tone for drama and thriller dialogue inserts."
        ),
    },
    {
        "provider_id": "VR6AewLTigWG4xSOukaG",
        "name": "Arnold",
        "language": "en",
        "gender": "male",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,deep,antagonist,thriller",
        "blurb": (
            "Deeper middle-aged male voice with gravity. "
            "Fits antagonists, threatening figures, or cold authoritative dialogue in horror and thriller."
        ),
    },
    {
        "provider_id": "pNInz6obpgDQGcFmaJgB",
        "name": "Adam",
        "language": "en",
        "gender": "male",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "narrator_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "narration,male,deep,english",
        "blurb": (
            "Deep American male narrator for serious drama and dark thriller arcs. "
            "Measured, cinematic, good for true-crime style framing."
        ),
    },
    {
        "provider_id": "yoZ06aMxZJJ28mfd3POQ",
        "name": "Sam",
        "language": "en",
        "gender": "male",
        "age": "young",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,young,raspy,character",
        "blurb": (
            "Young male with a slightly raspy edge. "
            "Useful for tense side characters, street-smart dialogue, or uneasy allies."
        ),
    },
    {
        "provider_id": "jBpfuIE2acCO8z3wKNLl",
        "name": "Gigi",
        "language": "en",
        "gender": "female",
        "age": "young",
        "accent": "american",
        "use_case": "animation",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "female,young,expressive,dialogue",
        "blurb": (
            "Expressive young female character voice. "
            "Works for animated emotional swings, panic, or lively dialogue in serial drama."
        ),
    },
    {
        "provider_id": "jsCqWAovK2LkecY7zXl4",
        "name": "Freya",
        "language": "en",
        "gender": "female",
        "age": "young",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "female,overcurious,character",
        "blurb": (
            "Curious young female voice with investigative energy. "
            "Good for journalist or inquisitive protagonist roles in mystery serials."
        ),
    },
    # Hindi-oriented casting blurbs using multilingual-capable library voices.
    # Same voice_ids may serve Hindi text via multilingual_v2 / v3.
    {
        "provider_id": "Xb7hH8MSUJpSbSDYk0k2",
        "name": "Alice",
        "language": "hi",
        "gender": "female",
        "age": "middle_aged",
        "accent": "british",
        "use_case": "narration",
        "asset_type": "narrator_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "hindi,narration,female,thriller,calm,mystery",
        "blurb": (
            "Hindi-capable female narrator for mystery and thriller serials. "
            "Calm measured Pocket FM style narration, clear diction, suitable for "
            "horror framing and suspenseful Hindi storytelling."
        ),
    },
    {
        "provider_id": "FGY2WhTYpPnrIDTdsKH5",
        "name": "Laura",
        "language": "hi",
        "gender": "female",
        "age": "young",
        "accent": "american",
        "use_case": "social_media",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "hindi,female,young,dialogue,emotional,horror",
        "blurb": (
            "Young Hindi-capable female character for emotional dialogue. "
            "Fits terrified, whispered, or intimate horror beats; Riya-type protagonist energy."
        ),
    },
    {
        "provider_id": "nPczCjzI2devNBz1zQrb",
        "name": "Brian",
        "language": "hi",
        "gender": "male",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "narrator_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "hindi,male,narration,deep,thriller",
        "blurb": (
            "Deep Hindi-capable male narrator for dark thriller and true-story framing. "
            "Authoritative, cinematic, good for multi-part serial openings."
        ),
    },
    {
        "provider_id": "iP95p4xoKVk53GoZ742B",
        "name": "Chris",
        "language": "hi",
        "gender": "male",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "conversational",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "hindi,male,dialogue,casual,character",
        "blurb": (
            "Conversational Hindi-capable male for natural dialogue inserts. "
            "Fits allies, husbands, or everyday characters in regional thriller serials."
        ),
    },
    {
        "provider_id": "onwK4e9ZLuTAKqWW03F9",
        "name": "Daniel",
        "language": "en",
        "gender": "male",
        "age": "middle_aged",
        "accent": "british",
        "use_case": "news",
        "asset_type": "narrator_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,british,news,authoritative,narration",
        "blurb": (
            "Authoritative British male, news-adjacent clarity. "
            "Useful for framed true-story narrators and factual horror introductions."
        ),
    },
    {
        "provider_id": "cgSgspJ2msmba13voRMb",
        "name": "Jessica",
        "language": "en",
        "gender": "female",
        "age": "young",
        "accent": "american",
        "use_case": "conversational",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "female,young,conversational,expressive",
        "blurb": (
            "Expressive young American female for conversational drama. "
            "Good for dialogue-forward scenes and emotional character turns."
        ),
    },
    {
        "provider_id": "cjVigY5qzO86Huf0OWal",
        "name": "Eric",
        "language": "en",
        "gender": "male",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "conversational",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,smooth,dialogue,thriller",
        "blurb": (
            "Smooth middle-aged male conversational voice. "
            "Fits charming antagonists or controlled thriller dialogue."
        ),
    },
    {
        "provider_id": "N2lVS1w4EtoT3dr4eOWO",
        "name": "Callum",
        "language": "en",
        "gender": "male",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "characters",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,hoarse,intense,horror,character",
        "blurb": (
            "Hoarse intense male character voice for horror. "
            "Ideal for threatening entities, the Voice, or distressed male leads."
        ),
    },
    {
        "provider_id": "IKne3meq5aG2GDUQ3HjG",
        "name": "Charlie",
        "language": "en",
        "gender": "male",
        "age": "middle_aged",
        "accent": "australian",
        "use_case": "conversational",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,casual,australian,dialogue",
        "blurb": (
            "Casual Australian-tinged male conversational voice. "
            "Useful for grounded side characters and everyday dialogue."
        ),
    },
    {
        "provider_id": "SAz9YHcvj6GT2YYXdZww",
        "name": "River",
        "language": "en",
        "gender": "neutral",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "narrator_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "neutral,narration,calm,relaxing",
        "blurb": (
            "Calm neutral narrator with relaxing clarity. "
            "Good for soft framing narration or dreamlike interstitial beats."
        ),
    },
    {
        "provider_id": "TX3LPaxmHKxFdv7VOQHJ",
        "name": "Liam",
        "language": "en",
        "gender": "male",
        "age": "young",
        "accent": "american",
        "use_case": "social_media",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,young,energetic,dialogue",
        "blurb": (
            "Energetic young male social-media style voice. "
            "Better for upbeat inserts than horror; use sparingly in thrillers."
        ),
    },
    {
        "provider_id": "bIHbv24MWmeRgasZH58o",
        "name": "Will",
        "language": "en",
        "gender": "male",
        "age": "young",
        "accent": "american",
        "use_case": "conversational",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,young,optimistic,dialogue",
        "blurb": (
            "Optimistic young male conversational voice for lighter character moments "
            "or contrast against darker thriller narration."
        ),
    },
    {
        "provider_id": "XrExE9yKIg1WjnnlVkGX",
        "name": "Matilda",
        "language": "en",
        "gender": "female",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "narrator_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "female,narration,warm,middle_aged",
        "blurb": (
            "Warm middle-aged female narrator. "
            "Fits mature storytelling, biopic framing, and emotionally grounded serial narration."
        ),
    },
    {
        "provider_id": "z9fAnlkpzviPz146aGWa",
        "name": "Glinda",
        "language": "en",
        "gender": "female",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "characters",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "female,witchy,character,horror",
        "blurb": (
            "Witchy theatrical female character voice. "
            "Useful for supernatural entities, eerie guides, or stylized horror characters."
        ),
    },
    {
        "provider_id": "ThT5KcBeYPX3keUQqHPh",
        "name": "Dorothy",
        "language": "en",
        "gender": "female",
        "age": "young",
        "accent": "british",
        "use_case": "narration",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "female,pleasant,british,dialogue",
        "blurb": (
            "Pleasant British young female voice. "
            "Good for composed characters, investigators, or soft-spoken dialogue."
        ),
    },
    {
        "provider_id": "ZQe5CZNOzWyzPSCn5a3c",
        "name": "James",
        "language": "en",
        "gender": "male",
        "age": "old",
        "accent": "australian",
        "use_case": "news",
        "asset_type": "narrator_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,old,calm,narration",
        "blurb": (
            "Calm older male narrator with news-like composure. "
            "Fits elder storyteller frames and reflective thriller closings."
        ),
    },
    {
        "provider_id": "MF3mGyEYCl7XYWbV9V6O",
        "name": "Elli",
        "language": "en",
        "gender": "female",
        "age": "young",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "female,young,emotional,dialogue",
        "blurb": (
            "Emotional young female voice for cry-adjacent and vulnerable dialogue beats "
            "in romance-thriller hybrids."
        ),
    },
    {
        "provider_id": "TxGEqnHWrfWFTfGW9XjX",
        "name": "Josh",
        "language": "en",
        "gender": "male",
        "age": "young",
        "accent": "american",
        "use_case": "narration",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "male,young,deep,dialogue",
        "blurb": (
            "Young deep male voice for intense character dialogue and cliffhanger lines."
        ),
    },
    {
        "provider_id": "VR6AewLTigWG4xSOukaG",
        "name": "Arnold Horror",
        "language": "hi",
        "gender": "male",
        "age": "middle_aged",
        "accent": "american",
        "use_case": "characters",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "hindi,male,deep,horror,antagonist,the_voice",
        "blurb": (
            "Hindi-capable deep threatening male for horror antagonist or 'The Voice'. "
            "Cold, heavy, suited to supernatural warnings and menacing dialogue."
        ),
    },
    {
        "provider_id": "EXAVITQu4vr4xnSDxMaL",
        "name": "Bella Horror HI",
        "language": "hi",
        "gender": "female",
        "age": "young",
        "accent": "american",
        "use_case": "characters",
        "asset_type": "character_voice",
        "free_users_allowed": True,
        "preview_url": None,
        "tags": "hindi,female,young,terrified,whisper,horror",
        "blurb": (
            "Hindi-capable soft young female for whispered terrified dialogue. "
            "Primary cast candidate for Riya-like horror protagonists."
        ),
    },
]


def curated_voice_rows() -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict] = []
    seen: set[str] = set()
    for v in CURATED_VOICES:
        # Allow same provider_id with different language/asset variants via composite id.
        row_id = f"voice_{v['provider_id']}_{v['language']}_{v['asset_type']}"
        if row_id in seen:
            continue
        seen.add(row_id)
        description = (
            f"{v['name']}. {v['blurb']} "
            f"Language: {v['language']}. Gender: {v['gender']}. Age: {v['age']}. "
            f"Accent: {v['accent']}. Use case: {v['use_case']}. "
            f"Tags: {v['tags']}. ElevenLabs voice_id={v['provider_id']}."
        )
        rows.append(
            {
                "id": row_id,
                "asset_type": v["asset_type"],
                "provider": "elevenlabs",
                "provider_id": v["provider_id"],
                "name": v["name"],
                "language": v["language"],
                "gender": v["gender"],
                "age": v["age"],
                "accent": v["accent"],
                "use_case": v["use_case"],
                "free_users_allowed": bool(v.get("free_users_allowed", True)),
                "preview_url": v.get("preview_url"),
                "tags": v.get("tags"),
                "description": description,
                "updated_at": now,
            }
        )
    return rows
