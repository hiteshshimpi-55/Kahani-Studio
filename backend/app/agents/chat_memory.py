"""Session chat memory graph — messages live in the Postgres checkpointer.

Mirrors synqed-playground: thread_id = session_id; history is the `messages`
channel on AsyncPostgresSaver (not a chat_turns table).
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict
from uuid import uuid4

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages


class ChatMemoryState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def _noop(state: ChatMemoryState) -> dict[str, Any]:
    """Input messages are merged by add_messages; node is a no-op."""
    return {}


def build_chat_memory_graph(checkpointer: BaseCheckpointSaver):
    g = StateGraph(ChatMemoryState)
    g.add_node("chat", _noop)
    g.set_entry_point("chat")
    g.add_edge("chat", END)
    return g.compile(checkpointer=checkpointer)


def thread_config(session_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": session_id}}


async def load_checkpoint_messages(
    checkpointer: BaseCheckpointSaver, session_id: str
) -> list[AnyMessage]:
    tup = await checkpointer.aget_tuple(thread_config(session_id))
    if tup is None:
        return []
    return list(tup.checkpoint.get("channel_values", {}).get("messages", []) or [])


async def append_turn(
    checkpointer: BaseCheckpointSaver,
    *,
    session_id: str,
    user_text: str,
    assistant_text: str,
    kind: str,
    run_id: str | None = None,
    questions: list[str] | None = None,
    analysis: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Persist one user + assistant turn into the session checkpoint."""
    graph = build_chat_memory_graph(checkpointer)
    user_id = str(uuid4())
    assistant_id = str(uuid4())
    human = HumanMessage(content=user_text, id=user_id)
    ai = AIMessage(
        content=assistant_text,
        id=assistant_id,
        additional_kwargs={
            "kind": kind,
            "run_id": run_id,
            "questions": questions or [],
            "analysis": analysis or {},
        },
    )
    await graph.ainvoke(
        {"messages": [human, ai]},
        thread_config(session_id),
    )
    return user_id, assistant_id


def messages_to_history_pairs(messages: list[AnyMessage]) -> list[dict[str, str]]:
    """Flatten checkpoint messages to {role, content} for the analyzer."""
    out: list[dict[str, str]] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": str(m.content or "")})
        elif isinstance(m, AIMessage):
            text = m.content if isinstance(m.content, str) else str(m.content or "")
            if text.strip():
                out.append({"role": "assistant", "content": text})
    return out
