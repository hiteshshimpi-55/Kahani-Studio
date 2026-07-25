"""ElevenLabs integration constants."""

STEM_SUBDIR = "tts"

# ── Free-tier premade voices tested for Hindi (eleven_v3 multilingual) ──
# Ranked by Hindi pronunciation clarity.  Every voice here is a premade
# that works on free-tier API keys with eleven_v3.
HINDI_FREE_VOICES: list[dict[str, str]] = [
    {"id": "pqHfZKP75CvOlQylNhV4", "name": "Bill",    "gender": "male",   "style": "wise, mature, narrator"},
    {"id": "onwK4e9ZLuTAKqWW03F9", "name": "Daniel",  "gender": "male",   "style": "steady, broadcaster, narrator"},
    {"id": "nPczCjzI2devNBz1zQrb", "name": "Brian",   "gender": "male",   "style": "deep, resonant, comforting"},
    {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam",    "gender": "male",   "style": "dominant, firm, commanding"},
    {"id": "cjVigY5qzO86Huf0OWal", "name": "Eric",    "gender": "male",   "style": "smooth, trustworthy"},
    {"id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "gender": "male",   "style": "deep, confident, energetic"},
    {"id": "iP95p4xoKVk53GoZ742B", "name": "Chris",   "gender": "male",   "style": "charming, down-to-earth, young"},
    {"id": "TX3LPaxmHKxFdv7VOQHJ", "name": "Liam",   "gender": "male",   "style": "energetic, young"},
    {"id": "JBFqnCBsd6RMkjVDRZzb", "name": "George",  "gender": "male",   "style": "warm, storyteller"},
    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah",  "gender": "female", "style": "mature, reassuring"},
    {"id": "Xb7hH8MSUJpSbSDYk0k2", "name": "Alice",  "gender": "female", "style": "clear, engaging"},
    {"id": "cgSgspJ2msm6clMCkdW9", "name": "Jessica", "gender": "female", "style": "playful, bright, warm"},
    {"id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily",   "gender": "female", "style": "velvety, actress"},
]

# Paid-plan Hindi Studio voices (Creator+ required for API).
PAID_HINDI_VOICES: dict[str, str] = {
    "NARRATOR": "ogCFP29Q71Wj6WHkN69b",  # Aakash Aryan
    "GANDHI": "nPczCjzI2devNBz1zQrb",     # Brian (fallback)
    "SURESH": "06llJPvI62CjqSWOX9Gp",     # Pari M
    "RIYA": "06llJPvI62CjqSWOX9Gp",       # Pari M
    "ARJUN": "pNInz6obpgDQGcFmaJgB",      # Adam
}
