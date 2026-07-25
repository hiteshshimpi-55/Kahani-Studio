"""Chat orchestrator — opinionated creative director, not a Q&A bot.

Flow: minimal input → discover (pitch plots) → user picks → generate.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.integrations.llm.client import chat_completion, resolve_llm_settings

logger = logging.getLogger(__name__)

ANALYZE_SYSTEM = """You are Kahani Studio's story director — opinionated, creative, proactive.

Given the user's latest message and conversation history, decide the next action.

Return ONLY valid JSON:
{
  "intent": "chat" | "generate",
  "action": "chat" | "discover" | "generate" | "rewrite" | "context_note",
  "reply": "your natural reply — be concise and creative, not robotic",
  "enough_context": boolean,
  "generation_brief": "concise brief if ready to write",
  "suggested_part_count": number or null,
  "plot_pitches": [
    {"title": "short title", "logline": "1-2 sentence pitch", "tone": "e.g. dark thriller"},
    ...
  ] or null
}

CRITICAL RULES:
- Be a CREATIVE DIRECTOR, not a helpdesk. Take initiative.
- action=chat for greetings, product questions, off-topic.
- action=discover when user wants ideas — even if the ask is vague
  ("suggest something", "I have a rough idea", "surprise me", genre/vibe only).
  Set plot_pitches to null — a research-backed step will generate the 3 pitches.
  Your reply should introduce them naturally: "Here are 3 ideas I'm excited about:"
- action=generate when user picks a plot OR gives a concrete scene/premise to write
  (including franchise/show references like "CID scene where Daya is shot").
  Set enough_context=true, fill generation_brief with the full premise.
  Do NOT skip research mentally — the server will web-research before writing.
- action=rewrite when user wants to revise/redo an existing script.
- action=context_note when user is just adding notes.
- NEVER ask more than 1 clarifying question. Prefer to fill gaps with creative choices.
- If user says "you discover" / "you decide" / "surprise me" — go straight to discover.
- Chat replies and discovery stay in English (or the user's language). Do NOT translate discovery into Hindi.
  Script language is handled later at write time (Hindi default unless user asked for English).
- NEVER mention source.md, Script Writer, discovery pipeline, LangGraph, or any internal system.
- Speak like a collaborator: "I love this direction" / "Here's what I'm thinking" — not a form.
"""

DISCOVER_SYSTEM = """You are a master storyteller for Pocket FM–style audio serials.

Given the user's brief PLUS web research (extraction + Tavily crawl), generate exactly 3 compelling plot pitches.

Return ONLY valid JSON:
{
  "pitches": [
    {
      "title": "Short punchy title (2-5 words)",
      "logline": "1-2 vivid sentences. Be specific — names, places, hooks. Make the listener NEED to hear it.",
      "tone": "e.g. dark psychological thriller, romantic suspense, gritty noir"
    },
    ...
  ],
  "reply": "A brief creative intro (1 sentence). Don't list the pitches — they'll be shown as cards."
}

Rules:
- Use discovery_extraction and web_research as creative fuel (similar works, real-world hooks, setting texture).
  Do NOT copy research verbatim; transform it into original audio-serial pitches.
- If the user brief is vague, lean on the research to invent concrete, binge-worthy directions.
- Each pitch must be DISTINCT — different angles on the genre.
- Be Pocket FM specific: cliffhangers, binge-worthy hooks, mass-appeal drama.
- Write pitches in English (titles, loglines, tones). Do NOT translate discovery into Hindi.
  Indian names/settings are fine when the story calls for them; language of the pitch text stays English
  unless the user explicitly asks for Hindi pitches.
- Make pitches specific enough that someone could start writing immediately.
- NEVER mention Tavily, crawl, extraction, or that you searched the web.
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


def _stub_analysis(user_message: str, attachment_count: int, history: list[dict[str, str]]) -> dict[str, Any]:
    lower = user_message.lower().strip()

    generate_hints = (
        "story", "script", "episode", "serial", "thriller", "romance",
        "horror", "write", "generate", "screenplay", "audio", "pocket",
        "part", "crime", "drama", "mystery", "comedy", "action",
    )
    wants = any(h in lower for h in generate_hints) and len(lower) > 8

    # "you decide" / "surprise me" / vague "suggest something" → discover
    delegate_hints = (
        "you decide",
        "you discover",
        "surprise me",
        "your choice",
        "up to you",
        "suggest",
        "pitch me",
        "ideas",
        "rough idea",
        "not sure",
    )
    delegating = any(h in lower for h in delegate_hints)

    # Check if user is picking a plot from prior pitches
    pick_hints = ("option", "first", "second", "third", "pick", "go with", "let's do", "choose", "number", "#1", "#2", "#3", "plot 1", "plot 2", "plot 3")
    picking = any(h in lower for h in pick_hints)

    # Check conversation history for prior pitches
    has_prior_pitches = any("plot_pitches" in str(turn.get("content", "")) for turn in history[-4:])

    if not wants and not delegating and not picking:
        return {
            "intent": "chat",
            "action": "chat",
            "reply": (
                "Hey! I'm your story director at Kahani Studio. "
                "Give me a genre and vibe — like 'crime thriller' or "
                "'romantic suspense set in Mumbai' — and I'll pitch you 3 killer plots."
            ),
            "enough_context": False,
            "generation_brief": "",
            "suggested_part_count": None,
            "plot_pitches": None,
        }

    if picking and has_prior_pitches:
        return {
            "intent": "generate",
            "action": "generate",
            "reply": "Great choice — I'm starting on the script now.",
            "enough_context": True,
            "generation_brief": user_message.strip(),
            "suggested_part_count": 1,
            "plot_pitches": None,
        }

    # Has genre/theme → discover (pitch plots)
    return {
        "intent": "generate",
        "action": "discover",
        "reply": "I've got some ideas brewing — here are 3 plots I'd love to write for you:",
        "enough_context": False,
        "generation_brief": user_message.strip(),
        "suggested_part_count": 1,
        "plot_pitches": [
            {
                "title": "The Midnight Witness",
                "logline": "A night-shift cab driver picks up a passenger who confesses to a murder — then realizes the driver saw everything from the crime scene CCTV. Now both are trapped in a ride where only one can walk away alive.",
                "tone": "dark thriller, claustrophobic tension",
            },
            {
                "title": "Blood Ledger",
                "logline": "An honest bank clerk discovers a hidden ledger linking her branch manager to a crime syndicate. When she reports it, she learns the police are in on it too — and she has 24 hours before the ledger disappears along with her.",
                "tone": "gritty financial crime, slow-burn suspense",
            },
            {
                "title": "The Confession Room",
                "logline": "A retired judge receives anonymous audio recordings of crimes he dismissed for lack of evidence — all with new proof. Each recording ends with: 'Your verdict was wrong. Fix it, or I will.' He has one week.",
                "tone": "psychological thriller, moral dilemma",
            },
        ],
    }


def _crawl_brief_for_pitches(crawl: Any) -> dict[str, Any]:
    """Compact Tavily crawl payload for the pitch LLM (not full CrawlResponse dump)."""
    similar = []
    for w in (getattr(crawl, "similar_works", None) or [])[:5]:
        similar.append(
            {
                "title": getattr(w, "title", "") or "",
                "snippet": (getattr(w, "snippet", "") or "")[:220],
            }
        )
    sources = []
    for w in (getattr(crawl, "all_sources", None) or [])[:6]:
        sources.append(
            {
                "title": getattr(w, "title", "") or "",
                "snippet": (getattr(w, "snippet", "") or "")[:180],
                "category": getattr(w, "category", "") or "",
            }
        )
    return {
        "topic_context": (getattr(crawl, "topic_context", "") or "")[:900],
        "similar_works": similar,
        "sources": sources,
    }


async def research_story_context(brief: str) -> dict[str, Any]:
    """Parminal extraction + Tavily crawl for chat discover AND generate.

    Returns discovery_brief, web_research, discovery_md, and research meta.
    Same stack LangGraph uses in discover_research.
    """
    from app.core.config import settings
    from app.integrations.llm.extraction import extract_content
    from app.services.extraction.markdown import to_markdown

    logger.info("story_research_start brief_chars=%d", len(brief or ""))
    extracted = extract_content(brief)
    discovery_brief: dict[str, Any] = {
        "topic": extracted.topic,
        "theme": extracted.theme,
        "setting": extracted.setting,
        "emotional_tone": extracted.emotional_tone,
        "narrative": extracted.narrative,
        "keywords": (extracted.keywords or [])[:12],
        "characters": [
            {"name": c.name, "role": c.role} for c in (extracted.characters or [])[:6]
        ],
    }
    logger.info(
        "story_research_extraction_ok topic=%r theme=%r",
        extracted.topic,
        extracted.theme,
    )

    crawl = None
    web_research: dict[str, Any] | None = None
    tavily_key = (settings.tavily_api_key or "").strip()
    if not tavily_key:
        logger.warning("story_research — TAVILY_API_KEY unset; extraction only")
    else:
        try:
            from app.integrations.tavily.client import crawl_for_extraction

            logger.info("story_research_tavily_start topic=%r", extracted.topic)
            crawl = crawl_for_extraction(extracted)
            web_research = _crawl_brief_for_pitches(crawl)
            logger.info(
                "story_research_tavily_ok topic=%r similar=%d sources=%d",
                extracted.topic,
                len(web_research.get("similar_works") or []),
                len(web_research.get("sources") or []),
            )
        except Exception:
            logger.exception("story_research_tavily_failed — continuing with extraction only")

    discovery_md = to_markdown(extracted, crawl)
    return {
        "discovery_brief": discovery_brief,
        "web_research": web_research,
        "discovery_md": discovery_md,
        "extraction": extracted.model_dump(mode="json"),
        "crawl": crawl.model_dump(mode="json") if crawl else None,
        "research": {
            "extraction": True,
            "tavily": crawl is not None,
            "topic": extracted.topic,
            "similar_works": len((web_research or {}).get("similar_works") or []),
            "sources": len((web_research or {}).get("sources") or []),
        },
    }


async def _research_for_pitches(brief: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Compat wrapper for pitch generation."""
    try:
        result = await research_story_context(brief)
        return result.get("discovery_brief") or {}, result.get("web_research")
    except Exception:
        logger.exception("discover_research_failed — pitching without research")
        return {}, None


async def generate_plot_pitches(
    *,
    user_message: str,
    history: list[dict[str, str]],
    attachment_count: int,
) -> dict[str, Any]:
    """Generate 3 vivid plot pitches using extraction + Tavily research + LLM."""
    _, api_key, _ = resolve_llm_settings()
    if not api_key:
        return {
            "pitches": [
                {
                    "title": "The Midnight Witness",
                    "logline": "A night-shift cab driver picks up a passenger who confesses to a murder — then realizes the driver saw everything from the CCTV. Now both are trapped in a ride where only one walks away.",
                    "tone": "dark thriller",
                },
                {
                    "title": "Blood Ledger",
                    "logline": "An honest bank clerk finds a hidden ledger linking her manager to a crime syndicate. When she reports it, the police are in on it — and she has 24 hours before she disappears.",
                    "tone": "gritty financial crime",
                },
                {
                    "title": "The Confession Room",
                    "logline": "A retired judge receives recordings of crimes he dismissed — with new proof. Each ends: 'Your verdict was wrong. Fix it, or I will.'",
                    "tone": "psychological thriller",
                },
            ],
            "reply": "Here are 3 crime stories I'd love to write for you — pick one and I'll start the script:",
            "research": {"extraction": False, "tavily": False, "topic": None},
        }

    transcript = []
    for turn in history[-6:]:
        role = turn.get("role") or "user"
        content = (turn.get("content") or "").strip()
        if content:
            transcript.append(f"{role}: {content}")

    # Vague prompts still get research: seed extract/crawl with brief + recent chat.
    research_seed = user_message.strip()
    if transcript:
        research_seed = (
            f"{user_message.strip()}\n\nRecent conversation:\n" + "\n".join(transcript[-4:])
        )

    discovery_brief: dict[str, Any] = {}
    web_research: dict[str, Any] | None = None
    try:
        discovery_brief, web_research = await _research_for_pitches(research_seed)
    except Exception:
        logger.exception("discover_research_failed — pitching without research")

    messages = [
        {"role": "system", "content": DISCOVER_SYSTEM},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "brief": user_message,
                    "conversation_context": transcript,
                    "attachment_count": attachment_count,
                    "discovery_extraction": discovery_brief or None,
                    "web_research": web_research,
                },
                ensure_ascii=False,
            ),
        },
    ]

    research_meta = {
        "extraction": bool(discovery_brief),
        "tavily": web_research is not None,
        "topic": discovery_brief.get("topic") if discovery_brief else None,
        "similar_works": len((web_research or {}).get("similar_works") or []),
        "sources": len((web_research or {}).get("sources") or []),
    }

    try:
        raw = await chat_completion(messages=messages, max_tokens=1200, temperature=0.85, json_mode=True)
        data = _extract_json(raw)
    except Exception:
        logger.exception("generate_plot_pitches LLM failed")
        return {
            "pitches": [],
            "reply": "I had trouble generating pitches — let me try a different approach.",
            "research": research_meta,
        }

    pitches = data.get("pitches", [])
    if not isinstance(pitches, list):
        pitches = []
    pitches = [
        {
            "title": str(p.get("title", "Untitled")),
            "logline": str(p.get("logline", "")),
            "tone": str(p.get("tone", "")),
        }
        for p in pitches[:3]
        if isinstance(p, dict) and p.get("logline")
    ]

    reply = str(data.get("reply", "")).strip()
    if not reply:
        reply = "Here are 3 directions I'm excited about — pick one and I'll start writing:"

    logger.info(
        "discover_pitches_done tavily=%s topic=%r pitches=%d",
        research_meta["tavily"],
        research_meta.get("topic"),
        len(pitches),
    )
    return {"pitches": pitches, "reply": reply, "research": research_meta}


async def analyze_user_message(
    *,
    user_message: str,
    history: list[dict[str, str]],
    attachment_count: int,
) -> dict[str, Any]:
    """Proactive analysis — discovers and pitches, doesn't endlessly clarify."""
    _, api_key, _ = resolve_llm_settings()
    if not api_key:
        return _stub_analysis(user_message, attachment_count, history)

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
        raw = await chat_completion(messages=messages, max_tokens=1500, temperature=0.5, json_mode=True)
        data = _extract_json(raw)
    except Exception:
        logger.exception("analyze_user_message LLM failed; using stub")
        return _stub_analysis(user_message, attachment_count, history)

    action = data.get("action")
    if action not in ("chat", "discover", "generate", "rewrite", "context_note"):
        intent = data.get("intent", "chat")
        enough = bool(data.get("enough_context"))
        pitches = data.get("plot_pitches")
        if pitches and isinstance(pitches, list) and len(pitches) > 0:
            action = "discover"
        elif intent == "generate" and enough:
            action = "generate"
        else:
            action = "chat"

    reply = str(data.get("reply") or "").strip()
    if not reply:
        if action == "discover":
            reply = "Here are some directions I'm thinking:"
        elif action == "generate":
            reply = "Starting on your script now."
        else:
            reply = "How can I help with your story today?"

    # Discover pitches are generated later with extraction + Tavily — ignore analyze-time cards.
    plot_pitches = None if action == "discover" else data.get("plot_pitches")

    return {
        "intent": data.get("intent", "chat"),
        "action": action,
        "reply": reply,
        "enough_context": bool(data.get("enough_context")),
        "generation_brief": str(data.get("generation_brief") or user_message).strip(),
        "suggested_part_count": data.get("suggested_part_count"),
        "plot_pitches": plot_pitches,
    }
