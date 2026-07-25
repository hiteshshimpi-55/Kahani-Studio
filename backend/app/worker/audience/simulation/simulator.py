"""Audience Simulator — Layer B: Persona-level listen simulation.

Runs part-level listen simulation for each synthetic persona:
  - Attention decay model
  - Skip impulse detection
  - P(continue) calculation
  - Share impulse
  - Drop reason assignment

This is a deterministic simulation engine (no LLM required).
LLM-enhanced simulation can be layered on top later.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from app.worker.audience.personas.models import Persona, PersonaSimResult


# ---------------------------------------------------------------------------
# Beat extraction
# ---------------------------------------------------------------------------

# Approximate chars per second of spoken audio
CHARS_PER_SECOND = 14


@dataclass
class Beat:
    """A story beat — a logical unit of narrative."""

    beat_id: str
    part: int
    text: str
    position_pct: float  # 0.0–1.0 within the part
    duration_sec: float


def extract_beats(script: str, part_count: int) -> list[Beat]:
    """Split script into beats (paragraph-level units) with timing metadata."""
    # Split into parts
    chunk_size = max(1, len(script) // part_count)
    parts_text = [script[i * chunk_size : (i + 1) * chunk_size] for i in range(part_count)]

    beats: list[Beat] = []
    for part_idx, part_text in enumerate(parts_text):
        # Split part into paragraphs (beats)
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", part_text) if p.strip()]
        if not paragraphs:
            paragraphs = [part_text.strip()] if part_text.strip() else []

        part_total_chars = sum(len(p) for p in paragraphs)

        running_chars = 0
        for beat_idx, para in enumerate(paragraphs):
            position_pct = running_chars / part_total_chars if part_total_chars > 0 else 0.0
            duration = len(para) / CHARS_PER_SECOND

            beats.append(
                Beat(
                    beat_id=f"p{part_idx + 1}_b{beat_idx + 1:02d}",
                    part=part_idx + 1,
                    text=para,
                    position_pct=position_pct,
                    duration_sec=duration,
                )
            )
            running_chars += len(para)

    return beats


# ---------------------------------------------------------------------------
# Engagement signals in text
# ---------------------------------------------------------------------------

TENSION_WORDS = re.compile(
    r"\b(suddenly|but|however|scream|danger|secret|reveal|shock|blood|dark|run|kill|dead)\b",
    re.IGNORECASE,
)
EMOTIONAL_WORDS = re.compile(
    r"\b(love|heart|tears|cry|miss|betray|promise|hope|dream)\b",
    re.IGNORECASE,
)
BORING_INDICATORS = re.compile(
    r"\b(meanwhile|and then|after that|later|the next day|some time passed)\b",
    re.IGNORECASE,
)
DIALOGUE_INDICATOR = re.compile(r'["""].*?["""]', re.DOTALL)


def _engagement_signal(beat: Beat) -> float:
    """Score how engaging a beat is (0.0 = boring, 1.0 = gripping)."""
    text = beat.text
    tension = len(TENSION_WORDS.findall(text)) * 0.15
    emotion = len(EMOTIONAL_WORDS.findall(text)) * 0.10
    boring = len(BORING_INDICATORS.findall(text)) * -0.20
    dialogue_bonus = 0.10 if DIALOGUE_INDICATOR.search(text) else 0.0

    # Position bonus — openings and endings are inherently more engaging
    position_bonus = 0.0
    if beat.position_pct < 0.1:  # Opening
        position_bonus = 0.15
    elif beat.position_pct > 0.85:  # Closing / cliff zone
        position_bonus = 0.20

    raw = 0.5 + tension + emotion + boring + dialogue_bonus + position_bonus
    return max(0.0, min(1.0, raw))


# ---------------------------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------------------------


def _intent_genre_affinity(intent: str, beats: list[Beat]) -> float:
    """How well does content match this persona's listening intent?"""
    full_text = " ".join(b.text for b in beats)

    affinity_patterns: dict[str, re.Pattern[str]] = {
        "romance_escape": re.compile(r"\b(love|heart|kiss|romance|dream|desire)\b", re.IGNORECASE),
        "thriller_binge": re.compile(r"\b(kill|dead|gun|chase|escape|danger|blood)\b", re.IGNORECASE),
        "true_story_curiosity": re.compile(r"\b(real|true|history|actual|based on)\b", re.IGNORECASE),
        "commute_passtime": re.compile(r".", re.IGNORECASE),  # universal — mild affinity
        "share_with_friends": re.compile(r"\b(twist|shock|reveal|unbelievable|crazy)\b", re.IGNORECASE),
    }

    pattern = affinity_patterns.get(intent)
    if not pattern or intent == "commute_passtime":
        return 0.6  # neutral baseline

    matches = len(pattern.findall(full_text))
    return min(1.0, 0.4 + matches * 0.05)


def simulate_persona_on_part(
    persona: Persona,
    beats: list[Beat],
    part_num: int,
    is_first_part: bool = False,
) -> PersonaSimResult:
    """Simulate one persona listening through one part.

    Models:
      - Attention decay: exponential decay modulated by engagement signals
      - Skip impulse: spikes when attention drops below skip_threshold
      - P(continue): based on final attention + cliff strength + intent match
      - Share impulse: based on peak engagement × share_propensity
    """
    if not beats:
        return PersonaSimResult(
            persona_id=persona.id,
            part=part_num,
            attention_decay=0.0,
            skip_impulse=1.0,
            p_continue=0.0,
            share_impulse=0.0,
            drop_reason="empty_content",
        )

    # --- Attention decay model ---
    attention = 1.0
    peak_engagement = 0.0
    peak_skip_impulse = 0.0
    worst_beat_id: str | None = None
    worst_attention = 1.0

    # Base decay rate per second of content
    base_decay_rate = 1.0 / persona.attention_span_sec
    intent_affinity = _intent_genre_affinity(persona.intent, beats)

    for beat in beats:
        engagement = _engagement_signal(beat)
        peak_engagement = max(peak_engagement, engagement)

        # Decay: faster when bored, slower when engaged
        effective_decay = base_decay_rate * beat.duration_sec * (1.5 - engagement)
        # Intent affinity reduces decay
        effective_decay *= (1.0 - intent_affinity * 0.3)

        attention = max(0.0, attention - effective_decay)

        # Recovery from high-engagement beats
        if engagement > 0.7:
            attention = min(1.0, attention + 0.05)

        # Track worst beat
        if attention < worst_attention:
            worst_attention = attention
            worst_beat_id = beat.beat_id

        # Skip impulse
        if attention < persona.skip_threshold:
            skip_impulse = (persona.skip_threshold - attention) / persona.skip_threshold
            peak_skip_impulse = max(peak_skip_impulse, skip_impulse)

    # --- P(continue) calculation ---
    # Factors: final attention, cliff strength (last beat engagement), intent match
    last_beat_engagement = _engagement_signal(beats[-1]) if beats else 0.0
    cliff_bonus = last_beat_engagement * 0.3

    # First part penalty — cold open must work harder
    first_part_penalty = -0.1 if is_first_part else 0.0

    p_continue = _sigmoid(
        attention * 2.0
        + cliff_bonus
        + intent_affinity * 0.5
        + first_part_penalty
        - 0.8  # centering offset
    )

    # --- Share impulse ---
    share_impulse = min(1.0, peak_engagement * persona.share_propensity * 3.0)

    # --- Drop reason ---
    drop_reason: str | None = None
    if p_continue < 0.4:
        if attention < 0.2:
            drop_reason = "attention_exhausted"
        elif peak_skip_impulse > 0.7:
            drop_reason = "skip_impulse_too_high"
        elif intent_affinity < 0.4:
            drop_reason = "content_intent_mismatch"
        elif is_first_part and last_beat_engagement < 0.4:
            drop_reason = "weak_cold_open"
        else:
            drop_reason = "gradual_disengagement"

    return PersonaSimResult(
        persona_id=persona.id,
        part=part_num,
        attention_decay=round(attention, 3),
        skip_impulse=round(peak_skip_impulse, 3),
        p_continue=round(p_continue, 3),
        share_impulse=round(share_impulse, 3),
        drop_reason=drop_reason,
        fragile_beat_id=worst_beat_id,
    )


def _sigmoid(x: float) -> float:
    """Standard sigmoid squashed to 0–1."""
    return 1.0 / (1.0 + math.exp(-x))


# ---------------------------------------------------------------------------
# Public batch API
# ---------------------------------------------------------------------------


class AudienceSimulator:
    """Run persona simulations across all parts of an episode."""

    def simulate(
        self,
        personas: list[Persona],
        script: str,
        part_count: int,
    ) -> list[PersonaSimResult]:
        """Simulate all personas against all parts. Returns flat list of results."""
        beats = extract_beats(script, part_count)

        # Group beats by part
        beats_by_part: dict[int, list[Beat]] = {}
        for beat in beats:
            beats_by_part.setdefault(beat.part, []).append(beat)

        results: list[PersonaSimResult] = []
        for persona in personas:
            for part_num in range(1, part_count + 1):
                part_beats = beats_by_part.get(part_num, [])
                result = simulate_persona_on_part(
                    persona=persona,
                    beats=part_beats,
                    part_num=part_num,
                    is_first_part=(part_num == 1),
                )
                results.append(result)

        return results
