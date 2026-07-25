"""Read session chat history from LangGraph checkpoints (synqed pattern)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.agents.chat_memory import load_checkpoint_messages
from app.schemas.projects.response import ChatHistoryItem


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content or "")


def assemble_chat_history(messages: list[AnyMessage]) -> list[dict[str, Any]]:
    """LangChain messages → flat history dicts (FE ChatHistoryItem fields)."""
    items: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    for m in messages:
        mid = getattr(m, "id", None) or str(id(m))
        if isinstance(m, HumanMessage):
            items.append(
                {
                    "id": str(mid),
                    "role": "user",
                    "content": _extract_text(m.content),
                    "kind": "user",
                    "created_at": now,
                    "run_id": None,
                    "questions": [],
                }
            )
            continue
        if isinstance(m, AIMessage):
            kwargs = m.additional_kwargs or {}
            questions = kwargs.get("questions") or []
            if not isinstance(questions, list):
                questions = []
            analysis = kwargs.get("analysis") or {}
            plot_pitches = analysis.get("plot_pitches") or []
            if not isinstance(plot_pitches, list):
                plot_pitches = []
            item: dict[str, Any] = {
                "id": str(mid),
                "role": "assistant",
                "content": _extract_text(m.content),
                "kind": str(kwargs.get("kind") or "reply"),
                "created_at": now,
                "run_id": kwargs.get("run_id"),
                "questions": [str(q) for q in questions],
            }
            if plot_pitches:
                item["plot_pitches"] = [
                    {"title": p.get("title", ""), "logline": p.get("logline", ""), "tone": p.get("tone", "")}
                    for p in plot_pitches
                    if isinstance(p, dict)
                ]
            items.append(item)
    return items


async def build_session_chat_history(
    checkpointer: BaseCheckpointSaver, session_id: str
) -> list[dict[str, Any]]:
    messages = await load_checkpoint_messages(checkpointer, session_id)
    return assemble_chat_history(messages)


def to_history_items(raw: list[dict[str, Any]]) -> list[ChatHistoryItem]:
    return [ChatHistoryItem(**row) for row in raw]
