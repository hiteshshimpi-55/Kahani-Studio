"""Layer A — Structural Audit (deterministic + rubric checks).

PRD §6.9 defines these checks:
  - hook ≤ 8s (opening hook must land within first ~200 chars)
  - open loop (every part must leave an unresolved thread)
  - dialogue ratio (balanced narration vs dialogue)
  - cliff diversity (no repetitive cliffhanger patterns)
  - cold-open clarity (first part setup must orient listener)

This module runs synchronously — no LLM calls. Pure heuristic scoring.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.worker.audience.audit.models import AuditScore, StructuralAuditResult


# ---------------------------------------------------------------------------
# Constants / thresholds
# ---------------------------------------------------------------------------

# Approximate chars per second of spoken audio (Hindi/English average)
CHARS_PER_SECOND = 14

# Hook must land within this many seconds
HOOK_MAX_SECONDS = 8
HOOK_MAX_CHARS = HOOK_MAX_SECONDS * CHARS_PER_SECOND  # ~112 chars

# Dialogue markers (simple heuristic — lines starting with speaker attribution)
DIALOGUE_PATTERN = re.compile(
    r'^[\s]*(?:"[^"]+"|"[^"]+"|[A-Z_]{2,}:\s)',
    re.MULTILINE,
)

# Open-loop indicators (questions, ellipsis, unresolved tension words)
OPEN_LOOP_SIGNALS = re.compile(
    r"(\?\s*$|\.{3}|—$|\bwhat if\b|\bbut then\b|\bsuddenly\b|\bwho\b.*\?)",
    re.MULTILINE | re.IGNORECASE,
)

# Cliffhanger type patterns
CLIFF_TYPES = {
    "question": re.compile(r"\?\s*$", re.MULTILINE),
    "revelation": re.compile(r"\b(reveal|truth|secret|real identity)\b", re.IGNORECASE),
    "threat": re.compile(r"\b(danger|kill|dead|attack|gun|knife)\b", re.IGNORECASE),
    "disappearance": re.compile(r"\b(vanish|disappear|gone|missing)\b", re.IGNORECASE),
    "emotional": re.compile(r"\b(heart|tears|love|betray)\b", re.IGNORECASE),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _PartText:
    part_num: int
    text: str


def _split_into_parts(script: str, part_count: int) -> list[_PartText]:
    """Split script into roughly equal parts.

    Tries to split on double-newlines (scene breaks) first; falls back to
    equal character splits.
    """
    # Look for explicit part markers like "--- Part 2 ---" or "## Part 2"
    part_markers = re.split(r"(?:^|\n)(?:---?\s*Part\s+\d+|##?\s*Part\s+\d+)", script, flags=re.IGNORECASE)
    if len(part_markers) >= part_count:
        parts = part_markers[:part_count]
    else:
        # Equal character split
        chunk_size = max(1, len(script) // part_count)
        parts = [script[i * chunk_size : (i + 1) * chunk_size] for i in range(part_count)]

    return [_PartText(part_num=i + 1, text=p.strip()) for i, p in enumerate(parts) if p.strip()]


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _score_hook(parts: list[_PartText]) -> AuditScore:
    """Check if part 1 has a strong hook within the first 8 seconds."""
    if not parts:
        return AuditScore(name="hook", score=0.0, comment="No script content")

    opening = parts[0].text[:HOOK_MAX_CHARS]

    # Heuristics: does the opening contain tension/question/action?
    tension_signals = len(OPEN_LOOP_SIGNALS.findall(opening))
    has_dialogue = bool(DIALOGUE_PATTERN.search(opening))
    has_action_words = bool(re.search(r"\b(run|scream|crash|bang|shot|blood|dark)\b", opening, re.IGNORECASE))

    score_points = min(1.0, (tension_signals * 0.3) + (0.2 if has_dialogue else 0) + (0.3 if has_action_words else 0))

    # Bonus if opening is concise (not a long exposition dump)
    word_count = len(opening.split())
    if word_count <= 25:
        score_points = min(1.0, score_points + 0.2)

    comment = f"Hook analysis: {tension_signals} tension signals, dialogue={'yes' if has_dialogue else 'no'}, {word_count} words in first {HOOK_MAX_SECONDS}s"
    return AuditScore(name="hook", score=round(score_points, 2), comment=comment)


def _score_pacing(parts: list[_PartText]) -> AuditScore:
    """Check pacing — penalize very uneven part lengths and monotonous text."""
    if len(parts) < 2:
        return AuditScore(name="pacing", score=0.5, comment="Single part — pacing N/A")

    lengths = [len(p.text) for p in parts]
    avg_len = sum(lengths) / len(lengths)
    max_deviation = max(abs(l - avg_len) / avg_len for l in lengths) if avg_len > 0 else 0

    # Score: 1.0 = perfectly even, 0.0 = one part is 3x+ others
    evenness = max(0.0, 1.0 - max_deviation)

    # Check for paragraph variety (rough proxy for pacing)
    paragraph_counts = [p.text.count("\n\n") + 1 for p in parts]
    avg_paras = sum(paragraph_counts) / len(paragraph_counts)
    variety_bonus = min(0.2, avg_paras * 0.03)

    score = min(1.0, evenness * 0.8 + variety_bonus)
    comment = f"Part lengths: {lengths}, max deviation {max_deviation:.0%} from mean"
    return AuditScore(name="pacing", score=round(score, 2), comment=comment)


def _score_dialogue_ratio(parts: list[_PartText]) -> AuditScore:
    """Check narration-to-dialogue balance (ideal: 55-80% narration for most series)."""
    full_text = "\n".join(p.text for p in parts)
    total_lines = [l for l in full_text.split("\n") if l.strip()]
    if not total_lines:
        return AuditScore(name="dialogue_ratio", score=0.0, comment="Empty script")

    dialogue_lines = [l for l in total_lines if DIALOGUE_PATTERN.match(l)]
    dialogue_pct = len(dialogue_lines) / len(total_lines)
    narration_pct = 1.0 - dialogue_pct

    # Sweet spot: narration 55–80%
    if 0.55 <= narration_pct <= 0.80:
        score = 1.0
    elif 0.40 <= narration_pct < 0.55 or 0.80 < narration_pct <= 0.90:
        score = 0.7
    else:
        score = 0.4

    comment = f"Narration {narration_pct:.0%} / Dialogue {dialogue_pct:.0%} ({len(dialogue_lines)}/{len(total_lines)} lines)"
    return AuditScore(name="dialogue_ratio", score=round(score, 2), comment=comment)


def _score_cliffhanger(parts: list[_PartText]) -> AuditScore:
    """Check cliff diversity — no repetitive cliffhanger patterns across parts."""
    if len(parts) < 2:
        return AuditScore(name="cliffhanger", score=0.5, comment="Single part — cliff check N/A")

    # Analyze the last ~150 chars of each part (the cliffhanger zone)
    cliff_zone_chars = 150
    cliff_types_used: list[set[str]] = []

    for part in parts[:-1]:  # Last part doesn't need a cliffhanger
        tail = part.text[-cliff_zone_chars:]
        types_found: set[str] = set()
        for cliff_type, pattern in CLIFF_TYPES.items():
            if pattern.search(tail):
                types_found.add(cliff_type)
        cliff_types_used.append(types_found)

    # Has cliffhanger at all?
    parts_with_cliff = sum(1 for t in cliff_types_used if t)
    coverage = parts_with_cliff / len(cliff_types_used) if cliff_types_used else 0

    # Diversity — how many distinct cliff types across parts?
    all_types = set()
    for t in cliff_types_used:
        all_types.update(t)
    diversity = min(1.0, len(all_types) / 3)  # 3+ distinct types = full marks

    score = coverage * 0.6 + diversity * 0.4
    comment = f"{parts_with_cliff}/{len(cliff_types_used)} parts have cliff, {len(all_types)} distinct types: {all_types or 'none'}"
    return AuditScore(name="cliffhanger", score=round(score, 2), comment=comment)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_structural_audit(script: str, part_count: int = 5) -> StructuralAuditResult:
    """Run the full structural audit (Layer A) on a script.

    Returns a StructuralAuditResult with scores for each rubric dimension.
    No LLM calls — pure heuristic analysis.
    """
    parts = _split_into_parts(script, part_count)

    hook = _score_hook(parts)
    pacing = _score_pacing(parts)
    dialogue = _score_dialogue_ratio(parts)
    cliffhanger = _score_cliffhanger(parts)

    overall = round(
        (hook.score * 0.30 + pacing.score * 0.20 + dialogue.score * 0.20 + cliffhanger.score * 0.30),
        2,
    )

    return StructuralAuditResult(
        overall_score=overall,
        hook_score=hook,
        pacing_score=pacing,
        dialogue_score=dialogue,
        cliffhanger_score=cliffhanger,
    )
