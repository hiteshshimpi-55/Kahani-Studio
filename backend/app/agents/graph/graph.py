"""Cancellable project graph runner with shared Postgres checkpointer."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.agents.graph.checkpointer import ensure_checkpoint_tables, get_checkpointer
from app.agents.graph.nodes_context import build_source, retrieve_context
from app.agents.graph.state import ProjectGraphState
from app.agents.script_writer.agent import ScriptWriterAgent, default_narration_config

logger = logging.getLogger(__name__)

CancelCheck = Callable[[], Awaitable[bool]]


class RunCancelled(Exception):
    """Raised when a project run is cancelled mid-graph."""


async def script_writer_node(state: ProjectGraphState) -> dict[str, Any]:
    agent = ScriptWriterAgent()
    narration = state.get("narration_config") or default_narration_config()
    package, screenplay = await agent.write(
        source_md=state.get("source_md") or "",
        narration_config=narration,
        part_count=state.get("part_count") or 4,
        total_duration_sec=state.get("total_duration_sec") or 600,
    )
    return {"script_package": package, "screenplay_md": screenplay}


def _noop_persist(state: ProjectGraphState) -> dict[str, Any]:
    return {}


def build_project_graph(*, checkpointer: Any | None = None):
    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        raise RuntimeError("langgraph is required") from exc

    graph = StateGraph(ProjectGraphState)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("build_source", build_source)
    graph.add_node("script_writer", script_writer_node)
    graph.add_node("persist_artifacts", _noop_persist)

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "build_source")
    graph.add_edge("build_source", "script_writer")
    graph.add_edge("script_writer", "persist_artifacts")
    graph.add_edge("persist_artifacts", END)
    return graph.compile(checkpointer=checkpointer)


async def run_project_graph(initial: ProjectGraphState, *, thread_id: str) -> ProjectGraphState:
    await ensure_checkpoint_tables()
    checkpointer = get_checkpointer()
    graph = build_project_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    result = await graph.ainvoke(initial, config)
    return result  # type: ignore[return-value]


async def run_project_graph_cancellable(
    initial: ProjectGraphState,
    *,
    is_cancelled: CancelCheck,
    thread_id: str,
) -> ProjectGraphState:
    """Run discovery → source → script writer; checkpoint after each node."""
    await ensure_checkpoint_tables()
    if await is_cancelled():
        raise RunCancelled()

    checkpointer = get_checkpointer()
    graph = build_project_graph(checkpointer=checkpointer)
    config: dict[str, Any] = {"configurable": {"thread_id": f"run:{thread_id}"}}

    try:
        async for _ in graph.astream(initial, config, stream_mode="updates"):
            if await is_cancelled():
                raise RunCancelled()
        snap = await graph.aget_state(config)
        values = snap.values if snap else {}
        if isinstance(values, dict) and values:
            return values  # type: ignore[return-value]
        result = await graph.ainvoke(None, config)
        return result  # type: ignore[return-value]
    except RunCancelled:
        raise
    except Exception:
        logger.exception("langgraph_stream_failed — falling back to node loop")
        return await _fallback_node_loop(initial, is_cancelled=is_cancelled)


async def _fallback_node_loop(
    initial: ProjectGraphState,
    *,
    is_cancelled: CancelCheck,
) -> ProjectGraphState:
    state: dict[str, Any] = dict(initial)
    steps: list[Callable[..., Any]] = [
        retrieve_context,
        build_source,
        script_writer_node,
        _noop_persist,
    ]
    for step in steps:
        if await is_cancelled():
            raise RunCancelled()
        result = step(state)  # type: ignore[arg-type]
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, dict):
            state.update(result)
    if await is_cancelled():
        raise RunCancelled()
    return state  # type: ignore[return-value]
