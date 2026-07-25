"""User-facing chat activity copy — hides internal LangGraph nodes."""

from __future__ import annotations

import random
from typing import Literal

ChatPhase = Literal[
    "thinking",
    "figuring",
    "context",
    "discovering",
    "writing",
    "rewriting",
    "polishing",
]

ChatAction = Literal["chat", "discover", "generate", "rewrite", "context_note"]

PHRASES: dict[ChatPhase, list[str]] = {
    "thinking": [
        "Reading your message…",
        "Taking this in…",
        "One moment…",
        "Hmm, let me see…",
        "Got it — thinking…",
    ],
    "figuring": [
        "Figuring out what you need…",
        "Choosing the best next step…",
        "Mapping your request…",
        "Weighing a few approaches…",
        "Finding the right angle…",
    ],
    "context": [
        "Glancing at what you've shared…",
        "Pulling from your project notes…",
        "Checking attached materials…",
        "Connecting the dots from your context…",
    ],
    "discovering": [
        "Researching the world of your story…",
        "Pulling references from the web…",
        "Exploring similar works and tone…",
        "Gathering discovery context…",
        "Dreaming up plots with research…",
        "Crafting plot pitches…",
    ],
    "writing": [
        "Writing your script…",
        "Shaping the opening beat…",
        "Finding the right voice…",
        "Drafting dialogue and turns…",
        "Building the episode arc…",
        "Letting the story breathe…",
        "Threading the cliffhangers…",
    ],
    "rewriting": [
        "Reworking the script…",
        "Applying your notes…",
        "Revising the draft…",
        "Tightening the beats…",
        "Reshaping what you flagged…",
    ],
    "polishing": [
        "Putting finishing touches on it…",
        "Almost there…",
        "Wrapping up…",
        "One last pass…",
    ],
}


def pick_phrase(phase: ChatPhase, *, seed: str | None = None) -> str:
    options = PHRASES.get(phase) or PHRASES["thinking"]
    if seed:
        rng = random.Random(seed)
        return rng.choice(options)
    return random.choice(options)


def phases_for_action(action: ChatAction, *, has_attachments: bool) -> list[ChatPhase]:
    """Status phases shown *before* the reply typewriter."""
    if action == "context_note":
        return ["thinking"]
    if action == "chat":
        return ["thinking"]
    if action == "discover":
        return ["thinking", "discovering"]
    if action == "rewrite":
        return ["thinking", "rewriting"]
    # generate — real Tavily research runs in stream (not a flash status)
    phases: list[ChatPhase] = ["thinking", "figuring"]
    if has_attachments:
        phases.append("context")
    return phases
