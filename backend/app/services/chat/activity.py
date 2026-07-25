"""User-facing chat activity copy — hides internal LangGraph nodes."""

from __future__ import annotations

import random
from typing import Literal

ChatPhase = Literal[
    "thinking",
    "figuring",
    "context",
    "writing",
    "rewriting",
    "polishing",
]

ChatAction = Literal["chat", "clarify", "generate", "rewrite", "context_note"]

PHRASES: dict[ChatPhase, list[str]] = {
    "thinking": [
        "Reading your message…",
        "Taking this in…",
        "One moment…",
    ],
    "figuring": [
        "Figuring out what you need…",
        "Choosing the best next step…",
        "Mapping your request…",
    ],
    "context": [
        "Pulling from your project context…",
        "Scanning attached materials…",
        "Checking what you've shared…",
    ],
    "writing": [
        "Writing your script…",
        "Shaping dialogue and beats…",
        "Drafting the audio screenplay…",
        "Building the episode structure…",
    ],
    "rewriting": [
        "Reworking the script…",
        "Applying your notes…",
        "Revising the draft…",
    ],
    "polishing": [
        "Putting finishing touches on it…",
        "Almost there…",
        "Wrapping up…",
    ],
}


def pick_phrase(phase: ChatPhase, *, seed: str | None = None) -> str:
    options = PHRASES.get(phase) or PHRASES["thinking"]
    if seed:
        rng = random.Random(seed)
        return rng.choice(options)
    return random.choice(options)


def phases_for_action(action: ChatAction, *, has_attachments: bool) -> list[ChatPhase]:
    """Which status phases to show — never expose raw graph node names."""
    if action == "context_note":
        return ["thinking"]
    if action in ("chat", "clarify"):
        phases: list[ChatPhase] = ["thinking", "figuring"]
        if has_attachments:
            phases.insert(1, "context")
        return phases
    if action == "rewrite":
        return ["thinking", "figuring", "rewriting"]
    # generate
    phases = ["thinking", "figuring"]
    if has_attachments:
        phases.append("context")
    phases.append("writing")
    return phases
