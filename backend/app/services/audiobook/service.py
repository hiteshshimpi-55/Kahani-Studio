"""ScriptPackage → cast voices → TTS stems → per-cue SFX → timeline mix.

Accepts any screenplay that follows the scripter format::

    SPEAKER: [direction] Dialogue text…
    [sfx: description of sound effect]

The parser preserves the **order** of lines and ``[sfx: …]`` cues so
that the final audio timeline mirrors the script exactly:

    stem → pause → sfx_clip → pause → stem → pause → …

SFX clips are generated individually per ``[sfx:]`` cue and placed
**between** dialogue — never layered on top of speech.  Speaker
changes get a longer silence gap so the listener can register the
voice switch.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.integrations.elevenlabs.client import get_elevenlabs_client
from app.integrations.elevenlabs.constants import HINDI_FREE_VOICES, PAID_HINDI_VOICES
from app.integrations.elevenlabs.sfx import generate_sound_effect
from app.schemas.cast.request import CastCharacter, CastScene, CastScript
from app.schemas.cast.response import CastReport
from app.schemas.tts.request import SynthesizeSpeechRequest, VoiceSettingsBody
from app.services.cast.service import CastService
from app.services.tts.service import TtsService

log = logging.getLogger(__name__)

# ── screenplay parsing (ordered events) ─────────────────────────────

_LINE_RE = re.compile(
    r"^(?P<speaker>[A-Za-z_][A-Za-z0-9_ ]*?):\s*"
    r"(?:\[(?P<direction>[^\]]*)\]\s*)?"
    r"(?P<text>.+)$",
)
_SFX_RE = re.compile(r"^\[sfx:\s*(?P<cue>[^\]]+)\]$", re.IGNORECASE)

WORDS_PER_SEC = 2.2

# ── humanised silence durations (seconds) ─────────────────────────
# These mimic how real audiobooks / movie dialogues breathe.
# A real conversation has ~1-2s between speakers; narration is slower.
PAUSE_BREATH = 0.5            # minimal breath within same speaker
PAUSE_SAME_SPEAKER = 0.75     # between consecutive sentences by same speaker
PAUSE_SPEAKER_CHANGE = 1.4    # different character takes over — a beat
PAUSE_NARRATOR_TO_CHAR = 1.1  # narrator hands off to a character
PAUSE_CHAR_TO_NARRATOR = 1.0  # character finishes, narrator resumes
PAUSE_AFTER_QUESTION = 1.6    # someone asked a question → thinking beat
PAUSE_AFTER_EXCLAMATION = 0.9 # urgency — shorter gap
PAUSE_DRAMATIC = 2.0          # after a dramatic beat / scene break
PAUSE_BEFORE_SFX = 0.6        # let the last word settle before SFX
PAUSE_AFTER_SFX = 0.9         # let the SFX ring out before speech resumes

# SFX clip length — short stingers between dialogue, not ambient beds
SFX_CLIP_SEC = 2.5
SFX_FADE_MS = 300             # fade-in and fade-out for SFX clips (ms)


class EventType(str, Enum):
    LINE = "line"
    SFX = "sfx"


@dataclass
class ScreenplayLine:
    speaker: str
    direction: str
    text: str
    seq_id: str


@dataclass
class ScreenplayEvent:
    type: EventType
    line: ScreenplayLine | None = None
    sfx_cue: str | None = None


@dataclass
class ParsedScreenplay:
    events: list[ScreenplayEvent] = field(default_factory=list)

    @property
    def lines(self) -> list[ScreenplayLine]:
        return [e.line for e in self.events if e.type == EventType.LINE and e.line]

    @property
    def inline_sfx_cues(self) -> list[str]:
        return [e.sfx_cue for e in self.events if e.type == EventType.SFX and e.sfx_cue]


def parse_screenplay(screenplay: str) -> ParsedScreenplay:
    """Parse screenplay into an ordered list of LINE and SFX events."""
    result = ParsedScreenplay()
    line_idx = 0
    for raw in screenplay.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or raw.startswith("_"):
            continue

        sfx_m = _SFX_RE.match(raw)
        if sfx_m:
            result.events.append(
                ScreenplayEvent(type=EventType.SFX, sfx_cue=sfx_m.group("cue").strip())
            )
            continue

        m = _LINE_RE.match(raw)
        if not m:
            continue

        text = m.group("text").strip()
        if not text:
            continue

        line_idx += 1
        line = ScreenplayLine(
            speaker=m.group("speaker").strip().upper().replace(" ", "_"),
            direction=(m.group("direction") or "").strip(),
            text=text,
            seq_id=f"l{line_idx:03d}",
        )
        result.events.append(ScreenplayEvent(type=EventType.LINE, line=line))

    return result


def slice_lines_for_duration(
    lines: list[ScreenplayLine], *, max_sec: float = 30.0
) -> list[ScreenplayLine]:
    """Keep lines until the word budget for *max_sec* is exhausted."""
    budget = int(max_sec * WORDS_PER_SEC)
    out: list[ScreenplayLine] = []
    words = 0
    for line in lines:
        w = max(1, len(line.text.split()))
        if out and words + w > budget:
            break
        out.append(line)
        words += w
        if words >= budget:
            break
    return out or lines[:1]


# ── v3 audio-tag helper ─────────────────────────────────────────────

def _build_character_base_tags(bible_chars: list[dict[str, Any]]) -> dict[str, str]:
    """Extract a short, stable vocal personality tag per character.

    This base tag is prepended to every line for that character, keeping
    the v3 model's voice in a consistent tonal lane.  The line-specific
    emotion tag is appended after it.
    """
    bases: dict[str, str] = {}
    for ch in bible_chars:
        cid = str(ch.get("id") or ch.get("name") or "").strip().upper().replace(" ", "_")
        if not cid:
            continue
        voice_desc = str(ch.get("voice") or "").strip()
        patterns = str(ch.get("speech_patterns") or "").strip()
        # distill to 2-3 words that define the character's vocal identity
        raw = f"{voice_desc}, {patterns}".lower() if voice_desc else patterns.lower()
        # pick the most meaningful personality words
        personality_words: list[str] = []
        for word in raw.replace(",", " ").split():
            word = word.strip()
            if word and word not in ("male", "female", "voice", "hindi",
                                     "english", "for", "and", "the", "a"):
                personality_words.append(word)
            if len(personality_words) >= 3:
                break
        bases[cid] = ", ".join(personality_words) if personality_words else ""
    return bases


def _v3_tagged_text(direction: str, text: str, *, base_tag: str = "") -> str:
    """Wrap spoken text with ElevenLabs v3 ``[direction]`` audio tag.

    If a ``base_tag`` is provided (the character's stable personality),
    it is prepended so the model keeps a consistent vocal identity.
    The line-specific ``direction`` is added after it.
    """
    direction = (direction or "").strip()
    if text.lstrip().startswith("["):
        return text

    # Merge base personality + line direction, deduplicating words
    base_words = [w.strip() for w in (base_tag or "").split(",") if w.strip()]
    dir_words = [w.strip() for w in direction.split(",") if w.strip()]
    seen: set[str] = set()
    merged: list[str] = []
    for w in base_words + dir_words:
        key = w.lower()
        if key not in seen:
            seen.add(key)
            merged.append(w)

    if not merged:
        return text
    return f"[{', '.join(merged)}] {text}"


# ── humanised pause calculator ──────────────────────────────────────

def _compute_pause(
    *,
    prev_speaker: str | None,
    prev_text: str | None,
    prev_was_sfx: bool,
    cur_speaker: str,
    narrator_ids: frozenset[str],
) -> float:
    """Return a context-aware silence duration (seconds).

    Mimics how humans breathe in conversation — the pause depends on
    what just happened and who is about to speak.
    """
    if prev_was_sfx:
        return PAUSE_AFTER_SFX

    if prev_speaker is None:
        return 0.0

    prev_upper = prev_speaker.upper()
    cur_upper = cur_speaker.upper()
    same = prev_upper == cur_upper
    prev_is_narrator = prev_upper in narrator_ids
    cur_is_narrator = cur_upper in narrator_ids

    last_char = (prev_text or "").rstrip()[-1:] if prev_text else ""

    if same:
        if last_char == "?":
            return PAUSE_SAME_SPEAKER + 0.2
        return PAUSE_SAME_SPEAKER

    # speaker changed
    if last_char == "?":
        return PAUSE_AFTER_QUESTION
    if last_char == "!":
        return PAUSE_AFTER_EXCLAMATION
    if prev_is_narrator and not cur_is_narrator:
        return PAUSE_NARRATOR_TO_CHAR
    if not prev_is_narrator and cur_is_narrator:
        return PAUSE_CHAR_TO_NARRATOR

    return PAUSE_SPEAKER_CHANGE


# ── voice stability mapping ─────────────────────────────────────────

_LOW_STABILITY_HINTS = frozenset(
    ["whisper", "nervous", "distort", "shaky", "trembling", "crying"]
)
_HIGH_STABILITY_HINTS = frozenset(
    ["calm", "measured", "guiding", "observational", "calmly"]
)


def _stability_for_direction(direction: str) -> float:
    """Map acting direction to ElevenLabs stability.

    We keep stability high (0.65-0.80) to ensure the same character
    sounds like the same person throughout.  Lower stability gives more
    expressiveness but risks making consecutive lines sound like
    different people — which listeners perceive as a voice change.
    """
    tokens = set(direction.lower().replace(",", " ").split())
    if tokens & _LOW_STABILITY_HINTS:
        return 0.55
    if tokens & _HIGH_STABILITY_HINTS:
        return 0.80
    return 0.70


def _speed_for_role(role: str, direction: str) -> float | None:
    """Narrator speaks slightly slower; characters at natural speed.

    Returns None to use the ElevenLabs default (1.0).
    """
    direction_lower = direction.lower() if direction else ""
    if "slow" in direction_lower:
        return 0.88
    if role == "narrator":
        return 0.92
    if "excited" in direction_lower or "urgent" in direction_lower:
        return 1.05
    return None


# ── ScriptPackage → CastScript ──────────────────────────────────────

def package_to_cast_script(
    package: dict[str, Any], *, series_id: str
) -> tuple[CastScript, list[str]]:
    """Build a ``CastScript`` from the scripter's output.

    Returns the CastScript *and* the merged list of SFX cues (inline +
    part-level) so the caller doesn't have to re-parse.
    """
    language = str(package.get("language") or "hi")
    bible_chars = (package.get("bible") or {}).get("characters") or []

    seen_ids: set[str] = set()
    characters: list[CastCharacter] = []

    for ch in bible_chars:
        name = str(ch.get("name") or ch.get("id") or "CHAR").strip()
        cid = str(ch.get("id") or name).strip().upper().replace(" ", "_")
        if cid in seen_ids:
            continue
        seen_ids.add(cid)

        role_raw = str(ch.get("role") or "character").lower()
        role = "narrator" if ("narrat" in role_raw or "guide" in role_raw) else "character"
        voice = str(ch.get("voice") or "")
        patterns = str(ch.get("speech_patterns") or "")
        casting_query = (
            f"{language} {role} voice for {name}. {voice}. {patterns}. "
            f"Pocket FM serial audiobook, expressive, clear."
        ).strip()

        characters.append(
            CastCharacter(id=cid, role=role, casting_query=casting_query,
                          traits=[t for t in [voice, patterns, role_raw] if t])
        )

    parts = package.get("parts") or []
    screenplay = str(parts[0].get("screenplay") or "") if parts else ""
    parsed = parse_screenplay(screenplay)

    for line in parsed.lines:
        if line.speaker in seen_ids:
            continue
        seen_ids.add(line.speaker)
        role = "narrator" if "NARR" in line.speaker else "character"
        characters.append(
            CastCharacter(
                id=line.speaker,
                role=role,
                casting_query=f"{language} {role} voice {line.speaker} audiobook serial",
            )
        )

    all_sfx: list[str] = list(parsed.inline_sfx_cues)
    if parts:
        part_cues = parts[0].get("sfx_cues") or []
        all_sfx.extend(str(c) for c in part_cues)
    seen_sfx: set[str] = set()
    unique_sfx: list[str] = []
    for cue in all_sfx:
        key = cue.strip().lower()
        if key and key not in seen_sfx:
            seen_sfx.add(key)
            unique_sfx.append(cue.strip())

    scenes: list[CastScene] = []
    if unique_sfx:
        scenes.append(
            CastScene(
                scene_id="s01",
                setting=str(parts[0].get("title") or "scene") if parts else "scene",
                sfx_query=", ".join(unique_sfx) + " ambience bed",
            )
        )

    if not characters:
        characters = [
            CastCharacter(
                id="NARRATOR",
                role="narrator",
                casting_query=f"{language} narrator calm audiobook serial",
            )
        ]

    return (
        CastScript(
            series_id=series_id,
            language=language,
            title=package.get("title"),
            characters=characters,
            scenes=scenes,
        ),
        unique_sfx,
    )


# ── voice assignment (deduplicated, Hindi-aware) ────────────────────

def _voice_map_from_cast(report: CastReport) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for ch in report.characters:
        if ch.primary and ch.primary.provider_id:
            mapping[ch.character_id.upper()] = ch.primary.provider_id
    return mapping


def _assign_voices(
    bible_chars: list[dict[str, Any]],
    cast_characters: list[CastCharacter],
    cast_map: dict[str, str],
    language: str,
    *,
    prefer_paid: bool = False,
) -> dict[str, str]:
    """Assign a distinct voice to every character.

    Priority order:
    1. ``voice_id`` explicitly set in the character bible → use directly
    2. Cast search result from vector DB → use if unique
    3. Curated free-tier pool → fill remaining characters

    This ensures the scripter can lock in specific voices while
    unknown characters still get auto-assigned.
    """
    assigned: dict[str, str] = {}
    used_ids: set[str] = set()

    # Pass 1: honour explicit voice_id from the bible
    for ch in bible_chars:
        vid = (ch.get("voice_id") or "").strip()
        if not vid:
            continue
        cid = str(ch.get("id") or ch.get("name") or "").strip().upper().replace(" ", "_")
        if cid:
            assigned[cid] = vid
            used_ids.add(vid)
            log.info("voice_from_bible %s → %s", cid, vid)

    # Pass 2: fill from cast search (deduplicated)
    for ch in cast_characters:
        key = ch.id.upper()
        if key in assigned:
            continue
        vid = cast_map.get(key)
        if vid and vid not in used_ids:
            assigned[key] = vid
            used_ids.add(vid)
            log.info("voice_from_cast %s → %s", key, vid)

    # Pass 3: fill remaining from curated pool
    is_hindi = (language or "").lower().startswith("hi")
    pool = list(HINDI_FREE_VOICES) if is_hindi else list(HINDI_FREE_VOICES)

    for ch in cast_characters:
        key = ch.id.upper()
        if key in assigned:
            continue
        role = (ch.role or "character").lower()
        # Try to match style (narrator gets narrator-style voices)
        for v in pool:
            if v["id"] in used_ids:
                continue
            if role == "narrator" and "narrator" not in v["style"]:
                continue
            assigned[key] = v["id"]
            used_ids.add(v["id"])
            log.info("voice_from_pool %s → %s (%s)", key, v["name"], v["style"])
            break
        # If no style match, take any unused
        if key not in assigned:
            for v in pool:
                if v["id"] not in used_ids:
                    assigned[key] = v["id"]
                    used_ids.add(v["id"])
                    log.info("voice_from_pool %s → %s (fallback)", key, v["name"])
                    break

    # Last resort: reuse first pool voice
    for ch in cast_characters:
        key = ch.id.upper()
        if key not in assigned:
            assigned[key] = pool[0]["id"]

    return assigned


def _deduplicate_cast_map(
    characters: list[CastCharacter],
    cast_map: dict[str, str],
) -> dict[str, str]:
    """Ensure no two characters share the same voice from cast search."""
    result = dict(cast_map)
    used: set[str] = set()
    dupes: list[str] = []

    for ch in characters:
        key = ch.id.upper()
        vid = result.get(key)
        if vid and vid not in used:
            used.add(vid)
        elif vid:
            dupes.append(key)

    if dupes:
        fallback_pool = [v["id"] for v in HINDI_FREE_VOICES if v["id"] not in used]
        for key in dupes:
            if fallback_pool:
                result[key] = fallback_pool.pop(0)
                log.info("voice_dedup %s → %s (was duplicate)", key, result[key])

    return result


def _match_voice(speaker: str, voice_map: dict[str, str], default: str) -> str:
    key = speaker.upper()
    if key in voice_map:
        return voice_map[key]
    for k, v in voice_map.items():
        if k in key or key in k:
            return v
    return default


# ── ffmpeg helpers ───────────────────────────────────────────────────

def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _generate_silence(dest: str, duration_sec: float) -> str:
    """Generate a silent mono 44100 Hz MP3 (matches ElevenLabs TTS output)."""
    dest_p = Path(dest)
    dest_p.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", f"{duration_sec:.2f}",
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(dest_p),
        ],
        check=True, capture_output=True,
    )
    return str(dest_p)


def _normalize_to_mono(src: str, dest: str, *, fade_ms: int = 0) -> str:
    """Convert any MP3 to mono 44100 Hz, optionally with fade-in/out."""
    dest_p = Path(dest)
    dest_p.parent.mkdir(parents=True, exist_ok=True)
    af_parts: list[str] = []
    if fade_ms > 0:
        fade_sec = fade_ms / 1000.0
        af_parts.append(f"afade=t=in:d={fade_sec:.2f}")
        af_parts.append(f"afade=t=out:st=-1:d={fade_sec:.2f}")
    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-ac", "1", "-ar", "44100",
    ]
    if af_parts:
        # fade-out needs the actual duration, use a two-pass approach
        # simpler: use acrossfade or just apply both fades
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", src],
            capture_output=True, text=True,
        )
        try:
            dur = float(probe.stdout.strip())
        except (ValueError, AttributeError):
            dur = SFX_CLIP_SEC
        fade_sec = fade_ms / 1000.0
        out_start = max(0, dur - fade_sec)
        af = f"afade=t=in:d={fade_sec:.2f},afade=t=out:st={out_start:.2f}:d={fade_sec:.2f}"
        cmd += ["-af", af]
    cmd += ["-c:a", "libmp3lame", "-b:a", "128k", str(dest_p)]
    subprocess.run(cmd, check=True, capture_output=True)
    return str(dest_p)


def _concat_segments(paths: list[str], dest: str) -> None:
    """Concat an ordered list of MP3 segments with re-encoding.

    Re-encodes instead of ``-c copy`` to avoid MP3 frame-boundary
    glitches that cause sentences to sound cut off.
    """
    dest_p = Path(dest)
    dest_p.parent.mkdir(parents=True, exist_ok=True)
    list_file = dest_p.with_suffix(".txt")
    list_file.write_text(
        "".join(f"file '{Path(p).resolve()}'\n" for p in paths),
        encoding="utf-8",
    )
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-ar", "44100", "-ac", "1",
                "-c:a", "libmp3lame", "-b:a", "128k",
                str(dest_p),
            ],
            check=True, capture_output=True,
        )
        log.info("concat_ok path=%s segments=%d", dest_p, len(paths))
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        log.warning("ffmpeg concat failed, falling back to byte-cat: %s", exc)
        with dest_p.open("wb") as out:
            for p in paths:
                out.write(Path(p).read_bytes())


def _loudnorm(src: str, dest: str) -> None:
    """Apply broadcast loudness normalization (keep mono 44100 Hz)."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "44100", "-ac", "1",
            "-c:a", "libmp3lame", "-b:a", "128k",
            dest,
        ],
        check=True, capture_output=True,
    )
    log.info("loudnorm_ok path=%s", dest)


# ── main service ─────────────────────────────────────────────────────

class AudiobookService:
    """Cast + ElevenLabs v3 TTS + per-cue SFX for a ScriptPackage preview.

    The output audio mirrors the screenplay timeline:

    1. Each ``SPEAKER: [dir] text`` → a TTS stem
    2. Each ``[sfx: cue]`` → a short SFX clip placed *between* dialogue
    3. Speaker changes get a longer silence gap
    4. SFX never overlaps dialogue
    """

    def render_preview(
        self,
        package: dict[str, Any],
        *,
        series_id: str = "audio_preview",
        max_sec: float = 120.0,
        concat: bool = True,
        with_sfx: bool = True,
        prefer_account_voices: bool = False,
    ) -> dict[str, Any]:
        parts = package.get("parts") or []
        if not parts:
            raise ValueError("ScriptPackage has no parts")

        screenplay = str(parts[0].get("screenplay") or "")
        parsed = parse_screenplay(screenplay)
        if not parsed.lines:
            raise ValueError("No SPEAKER: lines found in screenplay")

        # Keep only the lines that fit the duration budget
        allowed_lines = {
            ln.seq_id for ln in slice_lines_for_duration(parsed.lines, max_sec=max_sec)
        }
        language = str(package.get("language") or "hi")[:2]
        model_id = settings.elevenlabs_default_model_id

        # ── 1. Cast: find best voices ───────────────────────────────
        cast_script, sfx_cues = package_to_cast_script(package, series_id=series_id)
        log.info(
            "casting characters=%s language=%s model=%s",
            [c.id for c in cast_script.characters],
            cast_script.language, model_id,
        )

        report = CastService().recommend(cast_script)
        cast_map = _voice_map_from_cast(report)
        bible_chars = (package.get("bible") or {}).get("characters") or []
        voice_map = _assign_voices(
            bible_chars,
            cast_script.characters,
            cast_map,
            cast_script.language,
            prefer_paid=prefer_account_voices,
        )
        default_voice = settings.elevenlabs_default_voice_id
        log.info("voice_map=%s default=%s", voice_map, default_voice)

        # Stable vocal personality tag per character (from the bible).
        # This is prepended to every line's emotion direction so the v3
        # model keeps a consistent "voice lane" for each character.
        char_base_tags = _build_character_base_tags(bible_chars)
        log.info("char_base_tags=%s", char_base_tags)

        # ── 2. Walk events, synthesize stems + SFX clips ────────────
        out_dir = Path(settings.data_dir) / "tts" / series_id
        out_dir.mkdir(parents=True, exist_ok=True)

        tts = TtsService()
        el_client = get_elevenlabs_client() if with_sfx else None

        stems: list[dict[str, Any]] = []
        sfx_clips: list[dict[str, Any]] = []

        # timeline_segments: ordered list of MP3 paths for final concat
        timeline_segments: list[str] = []

        has_ffmpeg = _ffmpeg_available()

        # Silence cache — generate each unique duration only once
        _silence_cache: dict[str, str] = {}

        def _get_silence(dur: float) -> str:
            key = f"{dur:.2f}"
            if key not in _silence_cache:
                _silence_cache[key] = _generate_silence(
                    str(out_dir / f"_silence_{key}s.mp3"), dur
                )
            return _silence_cache[key]

        # Identify narrator character IDs for pause logic
        narrator_ids = frozenset(
            ch.id.upper()
            for ch in cast_script.characters
            if (ch.role or "").lower() in ("narrator", "guide")
        ) or frozenset({"NARRATOR"})

        # Build a quick role lookup for speed/style decisions
        role_by_id: dict[str, str] = {}
        for ch in cast_script.characters:
            role_by_id[ch.id.upper()] = (ch.role or "character").lower()

        # Deterministic seed per voice — locks the "randomness" so each
        # voice sounds consistent across all its segments in this episode.
        voice_seeds: dict[str, int] = {}
        for i, vid in enumerate(sorted(set(voice_map.values()))):
            voice_seeds[vid] = 1000 + i * 111

        prev_speaker: str | None = None
        prev_text: str | None = None
        prev_was_sfx = False
        sfx_idx = 0
        past_budget = False

        for event in parsed.events:
            # ── SFX event ───────────────────────────────────────────
            if event.type == EventType.SFX and event.sfx_cue:
                if past_budget or not with_sfx or not el_client or not has_ffmpeg:
                    continue

                sfx_idx += 1
                sfx_id = f"sfx_{sfx_idx:02d}"
                sfx_path = str(out_dir / f"{sfx_id}.mp3")
                cue = event.sfx_cue

                try:
                    sfx_prompt = f"{cue}, cinematic audio, high quality foley, no music, no voice"
                    sfx_bytes = generate_sound_effect(
                        el_client,
                        prompt=sfx_prompt,
                        duration_seconds=SFX_CLIP_SEC,
                        prompt_influence=0.6,
                    )
                    sfx_raw = str(out_dir / f"{sfx_id}_raw.mp3")
                    Path(sfx_raw).write_bytes(sfx_bytes)

                    _normalize_to_mono(sfx_raw, sfx_path, fade_ms=SFX_FADE_MS)

                    sfx_clips.append({
                        "sfx_id": sfx_id, "cue": cue,
                        "path": sfx_path,
                        "bytes": Path(sfx_path).stat().st_size,
                    })
                    log.info("sfx_clip %s cue=%s bytes=%d", sfx_id, cue[:60],
                             sfx_clips[-1]["bytes"])

                    if timeline_segments:
                        timeline_segments.append(_get_silence(PAUSE_BEFORE_SFX))
                    timeline_segments.append(sfx_path)
                    prev_was_sfx = True
                except Exception:
                    log.exception("sfx_clip_failed cue=%s — skipping", cue[:60])
                continue

            # ── LINE event ──────────────────────────────────────────
            if event.type == EventType.LINE and event.line:
                line = event.line
                if line.seq_id not in allowed_lines:
                    past_budget = True
                    continue

                voice_id = _match_voice(line.speaker, voice_map, default_voice)
                base_tag = char_base_tags.get(line.speaker.upper(), "")
                spoken = _v3_tagged_text(
                    line.direction, line.text, base_tag=base_tag,
                )
                stability = _stability_for_direction(line.direction)
                role = role_by_id.get(line.speaker.upper(), "character")
                speed = _speed_for_role(role, line.direction)

                result = tts.synthesize(
                    SynthesizeSpeechRequest(
                        text=spoken,
                        voice_id=voice_id,
                        model_id=model_id,
                        language_code=language,
                        series_id=series_id,
                        seq_id=line.seq_id,
                        seed=voice_seeds.get(voice_id),
                        voice_settings=VoiceSettingsBody(
                            stability=stability,
                            similarity_boost=0.85,
                            use_speaker_boost=True,
                            speed=speed,
                        ),
                    )
                )

                stem_size = Path(result.path).stat().st_size
                stems.append({
                    "seq_id": line.seq_id,
                    "speaker": line.speaker,
                    "direction": line.direction,
                    "text": line.text,
                    "spoken_text": spoken,
                    "voice_id": voice_id,
                    "path": result.path,
                    "bytes": stem_size,
                })
                log.info(
                    "stem %s speaker=%s voice=%s tag=%s spd=%s bytes=%d",
                    line.seq_id, line.speaker, voice_id,
                    line.direction or "-",
                    f"{speed:.2f}" if speed else "default",
                    stem_size,
                )

                # Humanised pause before this stem
                if timeline_segments and has_ffmpeg:
                    pause = _compute_pause(
                        prev_speaker=prev_speaker,
                        prev_text=prev_text,
                        prev_was_sfx=prev_was_sfx,
                        cur_speaker=line.speaker,
                        narrator_ids=narrator_ids,
                    )
                    if pause > 0:
                        timeline_segments.append(_get_silence(pause))

                timeline_segments.append(result.path)
                prev_speaker = line.speaker
                prev_text = line.text
                prev_was_sfx = False

        # ── 3. Assemble final timeline ──────────────────────────────
        preview_path = str(out_dir / "preview_30s.mp3")

        if concat and timeline_segments:
            raw_path = str(out_dir / "preview_raw.mp3")
            _concat_segments(timeline_segments, raw_path)

            if has_ffmpeg:
                try:
                    _loudnorm(raw_path, preview_path)
                except Exception:
                    log.exception("loudnorm failed — using raw concat")
                    Path(preview_path).write_bytes(Path(raw_path).read_bytes())
            else:
                Path(preview_path).write_bytes(Path(raw_path).read_bytes())

        return {
            "series_id": series_id,
            "title": package.get("title"),
            "language": language,
            "model_id": model_id,
            "max_sec": max_sec,
            "line_count": len(stems),
            "sfx_cue_count": len(sfx_cues),
            "sfx_clip_count": len(sfx_clips),
            "voice_map": voice_map,
            "cast": report.model_dump(mode="json"),
            "stems": stems,
            "sfx_clips": sfx_clips,
            "preview_mp3": preview_path if stems else None,
        }
