"""Chat orchestrator — clarify first, then discovery + script writer."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.integrations.llm.client import chat_completion, resolve_llm_settings

logger = logging.getLogger(__name__)

ANALYZE_SYSTEM = """You are Kahani Studio's story director assistant for Pocket FM–style audio serials.

Given the user's latest message and recent conversation, decide what to do next.

Return ONLY valid JSON with this shape:
{
  "intent": "chat" | "generate",
  "action": "chat" | "clarify" | "generate" | "rewrite",
  "needs_clarification": boolean,
  "questions": ["..."],
  "reply": "natural language reply to the user",
  "enough_context": boolean,
  "generation_brief": "concise brief to use as the generation prompt if ready, else empty",
  "suggested_part_count": number or null
}

Rules:
- action=chat for greetings/product questions.
- action=clarify when intent=generate but details missing.
- action=generate when ready to write a new script.
- action=rewrite when user wants to revise/redo an existing script or draft.
- If intent=generate but key details are missing (genre, language, tone, length/parts, premise), set needs_clarification=true and ask 1-3 short questions in "questions". Put a friendly intro in "reply".
- enough_context=true only when you can start discovery + script writing without more answers.
- Never invent that generation already started. You only analyze and ask or confirm readiness.
- Keep reply concise and collaborative.
"""


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {}


def _stub_analysis(user_message: str, attachment_count: int) -> dict[str, Any]:
    lower = user_message.lower().strip()
    generate_hints = (
        "story",
        "script",
        "episode",
        "serial",
        "thriller",
        "romance",
        "horror",
        "write",
        "generate",
        "screenplay",
        "audio",
        "pocket",
        "part",
    )
    wants = any(h in lower for h in generate_hints) and len(lower) > 12
    if not wants:
        return {
            "intent": "chat",
            "action": "chat",
            "needs_clarification": False,
            "questions": [],
            "reply": (
                "Hey — I can help you craft audio serial scripts for Kahani Studio. "
                "Tell me the premise, genre, language, and roughly how many parts you want, "
                "and I’ll clarify anything missing before we generate."
            ),
            "enough_context": False,
            "generation_brief": "",
            "suggested_part_count": None,
        }

    missing: list[str] = []
    if not any(x in lower for x in ("hindi", "english", "hinglish")):
        missing.append("Which language should this be in (Hindi, English, or Hinglish)?")
    if not any(x in lower for x in ("thriller", "romance", "horror", "drama", "comedy", "genre")):
        missing.append("What genre and tone are you going for?")
    if "part" not in lower and "episode" not in lower:
        missing.append("How many parts/episodes should we write (e.g. 1, 4, 8)?")
    if attachment_count == 0 and len(user_message.split()) < 40:
        missing.append(
            "Can you share more premise/plot detail, or attach a brief under Context?"
        )

    if missing:
        return {
            "intent": "generate",
            "action": "clarify",
            "needs_clarification": True,
            "questions": missing[:3],
            "reply": (
                "I can generate an audio script for that — I just need a bit more before discovery."
            ),
            "enough_context": False,
            "generation_brief": user_message.strip(),
            "suggested_part_count": 4,
        }

    return {
        "intent": "generate",
        "action": "generate",
        "needs_clarification": False,
        "questions": [],
        "reply": (
            "Great — I have enough to start. I’ll discover context, draft source.md, "
            "then run the Script Writer. You can stop anytime. When it’s done, you can save it as a draft."
        ),
        "enough_context": True,
        "generation_brief": user_message.strip(),
        "suggested_part_count": 4,
    }


async def analyze_user_message(
    *,
    user_message: str,
    history: list[dict[str, str]],
    attachment_count: int,
) -> dict[str, Any]:
    """Clarify-first analysis. Never starts generation itself."""
    _, api_key, _ = resolve_llm_settings()
    if not api_key:
        return _stub_analysis(user_message, attachment_count)

    transcript = []
    for turn in history[-8:]:
        role = turn.get("role") or "user"
        content = (turn.get("content") or "").strip()
        if content:
            transcript.append(f"{role}: {content}")

    messages = [
        {"role": "system", "content": ANALYZE_SYSTEM},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "latest_message": user_message,
                    "attachment_count": attachment_count,
                    "recent_conversation": transcript,
                },
                ensure_ascii=False,
            ),
        },
    ]

    try:
        raw = await chat_completion(messages=messages, max_tokens=900, temperature=0.4, json_mode=True)
        data = _extract_json(raw)
    except Exception:
        logger.exception("analyze_user_message LLM failed; using stub")
        return _stub_analysis(user_message, attachment_count)

    intent = data.get("intent") if data.get("intent") in ("chat", "generate") else "chat"
    questions = data.get("questions") if isinstance(data.get("questions"), list) else []
    questions = [str(q).strip() for q in questions if str(q).strip()][:4]
    reply = str(data.get("reply") or "").strip()
    needs = bool(data.get("needs_clarification"))
    enough = bool(data.get("enough_context"))
    brief = str(data.get("generation_brief") or "").strip() or user_message.strip()
    parts = data.get("suggested_part_count")
    part_count = int(parts) if isinstance(parts, int) and 1 <= parts <= 12 else None

    if intent == "generate" and needs and not questions:
        questions = [
            "What genre/tone should we use?",
            "Hindi, English, or Hinglish?",
            "How many parts should the script have?",
        ]
        enough = False

    if intent == "generate" and enough and needs:
        needs = False

    if not reply:
        reply = (
            "Could you share a bit more about what you’d like me to write?"
            if intent == "generate"
            else "How can I help with your story today?"
        )

    return {
        "intent": intent,
        "action": data.get("action") if data.get("action") in ("chat", "clarify", "generate", "rewrite") else (
            "clarify" if needs else ("generate" if intent == "generate" and enough else "chat")
        ),
        "needs_clarification": needs,
        "questions": questions,
        "reply": reply,
        "enough_context": enough and intent == "generate" and not needs,
        "generation_brief": brief,
        "suggested_part_count": part_count,
    }
