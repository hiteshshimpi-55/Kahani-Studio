"""Sarvam AI Bulbul v3 — full voice catalog for cast indexing.

Speaker list sourced from Sarvam docs / Bulbul v3 catalog (37 voices).
Hindi recommendations from official best-practices:
  Male: shubh, ashutosh · Female: priya, suhani
Storytelling use-case: shubh / roopa, pace 0.9, temperature 0.8
"""

from __future__ import annotations

from datetime import datetime, timezone

SARVAM_MODEL_ID = "bulbul:v3"

# Full Bulbul v3 catalog with rich casting descriptions.
# ``provider_id`` == speaker name (case-sensitive lowercase).
SARVAM_VOICES: list[dict[str, str]] = [
    # ── Male — Hindi recommended / storytelling ─────────────────────
    {
        "speaker": "shubh",
        "name": "Shubh",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "narrator_voice",
        "use_case": "narration,storytelling,audiobook,guide",
        "tags": "hindi,narrator,calm,clear,storyteller,top_rated,pocket_fm",
        "blurb": (
            "Top-rated Hindi male narrator. Calm, clear, measured cadence. "
            "Best default for Pocket FM / audiobook narration and historical storytelling. "
            "Official Sarvam Hindi male recommendation #1. "
            "Ideal for: NARRATOR, story guide, calm elder narrator."
        ),
    },
    {
        "speaker": "ashutosh",
        "name": "Ashutosh",
        "gender": "male",
        "age": "mature",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,authority,leader,elder",
        "tags": "hindi,mature,authoritative,deep,wise,commanding,elder,leader",
        "blurb": (
            "Mature, authoritative, deep Hindi male. Slow measured conviction. "
            "Official Sarvam Hindi male recommendation #2. "
            "Ideal for: elderly wise leaders, Gandhi-like figures, judges, gurus, "
            "commanding protagonists, father figures."
        ),
    },
    {
        "speaker": "ratan",
        "name": "Ratan",
        "gender": "male",
        "age": "adult",
        "accent": "indian",
        "asset_type": "narrator_voice",
        "use_case": "narration,professional,news,advisor",
        "tags": "hindi,english,professional,measured,confident,narrator,news",
        "blurb": (
            "Professional, measured, confident male. Strong Hindi and Indian English. "
            "Best English male voice; excellent for bilingual narration. "
            "Ideal for: professional narrators, advisors, news-style delivery, "
            "documentary voiceover."
        ),
    },
    {
        "speaker": "rohan",
        "name": "Rohan",
        "gender": "male",
        "age": "young",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,youth,ally,friend",
        "tags": "hindi,young,energetic,conversational,enthusiastic,ally",
        "blurb": (
            "Young energetic conversational Hindi male. Eager and passionate. "
            "Ideal for: youth joining a movement, friends, allies, sidekicks, "
            "enthusiastic young protagonists (e.g. Suresh-type characters)."
        ),
    },
    {
        "speaker": "varun",
        "name": "Varun",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "villain,antagonist,suspense,thriller",
        "tags": "hindi,deep,dramatic,intense,villain,suspense,thriller,NOT_neutral",
        "blurb": (
            "Deep, dramatic, intense villain/suspense voice. "
            "NOT suitable as a neutral default. Reserve exclusively for thriller, "
            "drama, antagonist, or suspense characters."
        ),
    },
    {
        "speaker": "rehan",
        "name": "Rehan",
        "gender": "male",
        "age": "adult",
        "accent": "indian",
        "asset_type": "narrator_voice",
        "use_case": "narration,gentle,calm,storytelling",
        "tags": "hindi,bengali,warm,gentle,calm,narrator,soft",
        "blurb": (
            "Warm, gentle, calm male. Top-rated for Bengali; strong Hindi. "
            "Ideal for: soft narrators, gentle mentors, emotional storytelling."
        ),
    },
    {
        "speaker": "mani",
        "name": "Mani",
        "gender": "male",
        "age": "adult",
        "accent": "indian",
        "asset_type": "character_voice",
        "use_case": "character,conversational,punjabi",
        "tags": "hindi,punjabi,warm,expressive,versatile,best_overall_male",
        "blurb": (
            "Warm expressive versatile male. Sarvam best male overall (Punjabi). "
            "Ideal for: general male characters, Punjabi-flavoured roles, "
            "warm conversational leads."
        ),
    },
    {
        "speaker": "aayan",
        "name": "Aayan",
        "gender": "male",
        "age": "young",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,youth,casual,everyday",
        "tags": "hindi,young,casual,friendly,everyday,conversational",
        "blurb": (
            "Young casual friendly Hindi male. Everyday conversational tone. "
            "Ideal for: ordinary young men, classmates, street-level characters."
        ),
    },
    {
        "speaker": "aditya",
        "name": "Aditya",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,conversational,lead",
        "tags": "hindi,adult,conversational,confident,lead",
        "blurb": (
            "Confident adult conversational Hindi male. Natural lead-character energy. "
            "Ideal for: adult male protagonists, romantic leads, urban professionals."
        ),
    },
    {
        "speaker": "advait",
        "name": "Advait",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,thoughtful,reflective",
        "tags": "hindi,thoughtful,reflective,calm,intellectual",
        "blurb": (
            "Thoughtful reflective Hindi male. Steady intellectual presence. "
            "Ideal for: writers, teachers, philosophers, contemplative characters."
        ),
    },
    {
        "speaker": "amit",
        "name": "Amit",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,everyday,conversational",
        "tags": "hindi,adult,everyday,reliable,conversational",
        "blurb": (
            "Reliable everyday Hindi male. Neutral conversational delivery. "
            "Ideal for: supporting cast, neighbours, colleagues, everyman roles."
        ),
    },
    {
        "speaker": "anand",
        "name": "Anand",
        "gender": "male",
        "age": "mature",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,warm,mature,father",
        "tags": "hindi,mature,warm,fatherly,kind",
        "blurb": (
            "Warm mature Hindi male with fatherly kindness. "
            "Ideal for: fathers, village elders, kind mentors, supportive uncles."
        ),
    },
    {
        "speaker": "dev",
        "name": "Dev",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,heroic,lead",
        "tags": "hindi,heroic,strong,lead,action",
        "blurb": (
            "Strong heroic Hindi male. Clear assertive delivery. "
            "Ideal for: action heroes, police officers, determined protagonists."
        ),
    },
    {
        "speaker": "gokul",
        "name": "Gokul",
        "gender": "male",
        "age": "adult",
        "accent": "indian",
        "asset_type": "character_voice",
        "use_case": "character,warm,south_indian",
        "tags": "hindi,warm,gentle,south_indian,friendly",
        "blurb": (
            "Warm gentle male with soft South-Indian flavour. "
            "Ideal for: friendly supporting cast, temple guides, soft-spoken allies."
        ),
    },
    {
        "speaker": "kabir",
        "name": "Kabir",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,poetic,intense",
        "tags": "hindi,poetic,intense,emotional,artist",
        "blurb": (
            "Poetic intense Hindi male. Emotional artistic colour. "
            "Ideal for: poets, artists, passionate lovers, dramatic monologues."
        ),
    },
    {
        "speaker": "manan",
        "name": "Manan",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,warm,versatile",
        "tags": "hindi,warm,expressive,versatile,side_character",
        "blurb": (
            "Warm expressive versatile Hindi male. Good all-round side character. "
            "Ideal for: friends, cousins, flexible supporting roles."
        ),
    },
    {
        "speaker": "mohit",
        "name": "Mohit",
        "gender": "male",
        "age": "young",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,youth,urban",
        "tags": "hindi,young,urban,modern,casual",
        "blurb": (
            "Young urban modern Hindi male. Casual city energy. "
            "Ideal for: college students, startup workers, city youth."
        ),
    },
    {
        "speaker": "rahul",
        "name": "Rahul",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,friendly,everyday",
        "tags": "hindi,friendly,approachable,everyday",
        "blurb": (
            "Friendly approachable Hindi male. Neutral everyday tone. "
            "Ideal for: neighbours, shopkeepers, approachable supporting cast."
        ),
    },
    {
        "speaker": "soham",
        "name": "Soham",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,calm,sincere",
        "tags": "hindi,calm,sincere,grounded,honest",
        "blurb": (
            "Calm sincere grounded Hindi male. Honest delivery. "
            "Ideal for: truthful witnesses, earnest friends, sincere protagonists."
        ),
    },
    {
        "speaker": "sumit",
        "name": "Sumit",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,professional,office",
        "tags": "hindi,professional,office,clear,corporate",
        "blurb": (
            "Clear professional Hindi male. Corporate/office presence. "
            "Ideal for: managers, bureaucrats, office colleagues."
        ),
    },
    {
        "speaker": "sunny",
        "name": "Sunny",
        "gender": "male",
        "age": "young",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,cheerful,youth",
        "tags": "hindi,cheerful,bright,youthful,upbeat",
        "blurb": (
            "Cheerful bright youthful Hindi male. Upbeat energy. "
            "Ideal for: comic relief, optimistic friends, light-hearted roles."
        ),
    },
    {
        "speaker": "tarun",
        "name": "Tarun",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,steady,reliable",
        "tags": "hindi,steady,reliable,mature_adult",
        "blurb": (
            "Steady reliable Hindi male. Solid mid-range adult voice. "
            "Ideal for: dependable allies, soldiers, steady supporting leads."
        ),
    },
    {
        "speaker": "vijay",
        "name": "Vijay",
        "gender": "male",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,strong,bold",
        "tags": "hindi,strong,bold,assertive,action",
        "blurb": (
            "Strong bold assertive Hindi male. Action-ready presence. "
            "Ideal for: warriors, activists, bold protagonists."
        ),
    },
    # ── Female — Hindi recommended / storytelling ───────────────────
    {
        "speaker": "priya",
        "name": "Priya",
        "gender": "female",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "narrator_voice",
        "use_case": "narration,protagonist,storytelling,lead",
        "tags": "hindi,warm,natural,expressive,top_rated,narrator,protagonist",
        "blurb": (
            "Top-rated Hindi female. Warm, natural, expressive. "
            "Excellent across Hindi, Telugu, Kannada, Tamil, Marathi, Gujarati, English. "
            "Official Sarvam Hindi female recommendation #1. "
            "Ideal for: female narrators, lead protagonists, emotional storytelling."
        ),
    },
    {
        "speaker": "suhani",
        "name": "Suhani",
        "gender": "female",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "narrator_voice",
        "use_case": "narration,calm,guide,wellness",
        "tags": "hindi,soft,gentle,warm,calm,narrator,wellness",
        "blurb": (
            "Soft gentle warm Hindi female. Official Hindi female recommendation #2. "
            "Ideal for: calm narrators, wellness/meditation guides, gentle mentors."
        ),
    },
    {
        "speaker": "ishita",
        "name": "Ishita",
        "gender": "female",
        "age": "adult",
        "accent": "indian",
        "asset_type": "narrator_voice",
        "use_case": "narration,professional,news",
        "tags": "hindi,english,clear,professional,articulate,news,narrator",
        "blurb": (
            "Clear professional articulate female. Best English female; strong Hindi. "
            "Ideal for: news-style narration, documentary VO, professional guides."
        ),
    },
    {
        "speaker": "roopa",
        "name": "Roopa",
        "gender": "female",
        "age": "adult",
        "accent": "indian",
        "asset_type": "narrator_voice",
        "use_case": "narration,storytelling,dramatic",
        "tags": "hindi,bengali,expressive,dramatic,storyteller,audiobook",
        "blurb": (
            "Expressive dramatic storyteller female. Recommended for storytelling use-case. "
            "Strong Hindi and Bengali. Ideal for: audiobook narration, dramatic tales, "
            "folk-story tellers."
        ),
    },
    {
        "speaker": "ritu",
        "name": "Ritu",
        "gender": "female",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,friend,ally",
        "tags": "hindi,warm,conversational,friendly,all_rounder",
        "blurb": (
            "Warm conversational friendly Hindi female. Good all-rounder. "
            "Ideal for: friends, allies, sisters, supportive female cast."
        ),
    },
    {
        "speaker": "neha",
        "name": "Neha",
        "gender": "female",
        "age": "young",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,youth,enthusiastic",
        "tags": "hindi,energetic,bright,youthful,enthusiastic",
        "blurb": (
            "Energetic bright youthful Hindi female. High enthusiasm. "
            "Ideal for: young female protagonists, college friends, cheerful allies."
        ),
    },
    {
        "speaker": "pooja",
        "name": "Pooja",
        "gender": "female",
        "age": "adult",
        "accent": "indian",
        "asset_type": "narrator_voice",
        "use_case": "narration,wellness,meditation,calm",
        "tags": "hindi,gentle,soothing,calm,meditation,wellness",
        "blurb": (
            "Gentle soothing calm female. Excellent for wellness and meditation. "
            "Ideal for: calming narrators, spiritual guides, soft bedtime stories."
        ),
    },
    {
        "speaker": "shreya",
        "name": "Shreya",
        "gender": "female",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "narrator_voice",
        "use_case": "narration,professional,news",
        "tags": "hindi,bright,clear,articulate,professional,news",
        "blurb": (
            "Bright clear articulate Hindi female. Strong diction. "
            "Ideal for: professional narration, news briefs, educational content."
        ),
    },
    {
        "speaker": "kavitha",
        "name": "Kavitha",
        "gender": "female",
        "age": "adult",
        "accent": "indian",
        "asset_type": "character_voice",
        "use_case": "character,warm,south_indian",
        "tags": "hindi,warm,mature,south_indian,motherly",
        "blurb": (
            "Warm mature female with South-Indian flavour. Motherly presence. "
            "Ideal for: mothers, aunties, warm village women."
        ),
    },
    {
        "speaker": "kavya",
        "name": "Kavya",
        "gender": "female",
        "age": "young",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,youth,soft",
        "tags": "hindi,young,soft,gentle,romantic",
        "blurb": (
            "Young soft gentle Hindi female. Soft romantic colour. "
            "Ideal for: young romantic leads, shy protagonists, soft-spoken girls."
        ),
    },
    {
        "speaker": "rupali",
        "name": "Rupali",
        "gender": "female",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,expressive,emotional",
        "tags": "hindi,expressive,emotional,dramatic",
        "blurb": (
            "Expressive emotional Hindi female. Strong dramatic range. "
            "Ideal for: emotional climaxes, grieving mothers, dramatic heroines."
        ),
    },
    {
        "speaker": "shruti",
        "name": "Shruti",
        "gender": "female",
        "age": "adult",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,clear,intelligent",
        "tags": "hindi,clear,intelligent,sharp,professional",
        "blurb": (
            "Clear intelligent sharp Hindi female. Professional edge. "
            "Ideal for: journalists, lawyers, sharp-witted female leads."
        ),
    },
    {
        "speaker": "simran",
        "name": "Simran",
        "gender": "female",
        "age": "young",
        "accent": "indian",
        "asset_type": "character_voice",
        "use_case": "character,youth,punjabi,warm",
        "tags": "hindi,punjabi,young,warm,lively",
        "blurb": (
            "Young warm lively female with Punjabi flavour. "
            "Ideal for: Punjabi girls, lively friends, festive characters."
        ),
    },
    {
        "speaker": "tanya",
        "name": "Tanya",
        "gender": "female",
        "age": "young",
        "accent": "indian_hindi",
        "asset_type": "character_voice",
        "use_case": "character,youth,modern,urban",
        "tags": "hindi,young,modern,urban,confident",
        "blurb": (
            "Young modern urban confident Hindi female. "
            "Ideal for: city girls, modern professionals, confident young leads."
        ),
    },
]

# Back-compat alias used by local pool fallback in audiobook service
SARVAM_HINDI_VOICES = [
    {
        "speaker": v["speaker"],
        "gender": v["gender"],
        "style": ", ".join(v["tags"].split(",")[:3]),
        "best_for": v["use_case"].replace(",", ", "),
        "notes": v["blurb"][:120],
    }
    for v in SARVAM_VOICES
]


def sarvam_voice_rows() -> list[dict]:
    """Normalize Sarvam voices into cast_assets rows for Databricks Vector Search."""
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict] = []
    seen: set[str] = set()

    for v in SARVAM_VOICES:
        speaker = v["speaker"]
        for language in ("hi", "en"):
            row_id = f"sarvam_{speaker}_{language}_{v['asset_type']}"
            if row_id in seen:
                continue
            seen.add(row_id)

            lang_label = "Hindi (hi-IN)" if language == "hi" else "Indian English (en-IN)"
            priority = (
                "PRIMARY CAST PREFERENCE — native Indian TTS (Sarvam Bulbul v3). "
                "Prefer this over ElevenLabs for Hindi and Indian-language audiobooks."
            )
            description = (
                f"{v['name']} (Sarvam Bulbul v3). {v['blurb']} "
                f"{priority} "
                f"Language: {lang_label}. Gender: {v['gender']}. Age: {v['age']}. "
                f"Accent: {v['accent']}. Use case: {v['use_case']}. "
                f"Tags: {v['tags']}. "
                f"Provider: sarvam. Model: {SARVAM_MODEL_ID}. "
                f"Speaker/provider_id={speaker}."
            )
            rows.append(
                {
                    "id": row_id,
                    "asset_type": v["asset_type"],
                    "provider": "sarvam",
                    "provider_id": speaker,
                    "name": f"{v['name']} (Sarvam)",
                    "language": language,
                    "gender": v["gender"],
                    "age": v["age"],
                    "accent": v["accent"],
                    "use_case": v["use_case"],
                    "free_users_allowed": True,
                    "preview_url": None,
                    "tags": f"sarvam|{v['tags']}|model:{SARVAM_MODEL_ID}|priority:primary",
                    "description": description,
                    "updated_at": now,
                }
            )

    return rows
