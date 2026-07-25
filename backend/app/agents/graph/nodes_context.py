from __future__ import annotations

import logging
from typing import Any

from app.agents.graph.state import ProjectGraphState
from app.integrations.databricks_ai_search import AISearchClient
from app.services.projects.storage import runs_dir

logger = logging.getLogger(__name__)


def retrieve_context(state: ProjectGraphState) -> dict[str, Any]:
    client = AISearchClient()
    chunks = client.similarity_search(
        project_id=state["project_id"],
        query_text=state["prompt"],
        top_k=8,
    )
    return {"retrieved_chunks": chunks}


def _format_cast(cast: list[dict[str, Any]]) -> list[str]:
    if not cast:
        return ["_No series cast yet — invent a tight multicast bible for this episode._"]
    lines: list[str] = []
    for ch in cast:
        name = ch.get("name") or ch.get("character_key") or "UNKNOWN"
        role = ch.get("role") or ""
        voice = ch.get("voice") or ""
        patterns = ch.get("speech_patterns") or ""
        arc = ch.get("arc") or ""
        key = ch.get("character_key") or ch.get("id") or ""
        lines.append(
            f"- **{name}** (id={key}, role={role})\n"
            f"  voice: {voice}\n"
            f"  speech_patterns: {patterns}\n"
            f"  arc: {arc}"
        )
    lines.append("")
    lines.append(
        "Reuse these characters (same ids/names/voices). Only add new characters if the story needs them."
    )
    return lines


def _format_episode(ep: dict[str, Any], *, label: str) -> list[str]:
    part_no = ep.get("part_number") or "?"
    title = ep.get("title") or f"Episode {part_no}"
    cliff = ep.get("cliff_out") or ""
    excerpt = (ep.get("screenplay_excerpt") or "").strip()
    lines = [
        f"### {label}: Part {part_no} — {title}",
        "",
    ]
    if cliff:
        lines.append(f"**Cliff out:** {cliff}")
        lines.append("")
    if excerpt:
        lines.append("**Screenplay excerpt:**")
        lines.append("")
        lines.append(excerpt)
        lines.append("")
    return lines


def build_source(state: ProjectGraphState) -> dict[str, Any]:
    part_number = state.get("part_number") or 1
    duration = state.get("total_duration_sec") or 90
    cast = state.get("series_cast") or []
    continuity = state.get("continuity_episodes") or []

    lines = [
        "# Generation brief",
        "",
        "## User prompt",
        "",
        state["prompt"].strip(),
        "",
        "## Episode request",
        "",
        f"- part_number: {part_number}",
        f"- target_duration_sec: {duration}",
        "- Write exactly ONE episode/part for this request.",
        "- Script language: hi (Hindi) unless the user prompt explicitly requests English.",
        "- Write the screenplay / dialogue / narration in that script language.",
        "- Discovery research below may be in English — do NOT translate research notes into Hindi; use them as English context only.",
        "",
        "## Series cast (locked)",
        "",
    ]
    lines.extend(_format_cast(list(cast)))
    lines.append("")

    latest = next((e for e in continuity if e.get("is_latest")), None)
    pinned = [e for e in continuity if e.get("pinned") and not e.get("is_latest")]

    lines.append("## Continuity — previous episode")
    lines.append("")
    if latest:
        lines.extend(_format_episode(latest, label="Latest"))
        lines.append(
            "Continue from this cliff. Do not reset the cast or contradict established facts."
        )
    else:
        lines.append("_No prior saved episode — this is the series opener._")
    lines.append("")

    if pinned:
        lines.append("## Pinned episodes")
        lines.append("")
        for ep in pinned:
            lines.extend(_format_episode(ep, label="Pinned"))
        lines.append("")

    lines.append("## Retrieved documents")
    lines.append("")
    chunks = state.get("retrieved_chunks") or []
    if not chunks:
        lines.append("_No attachment context retrieved._")
    else:
        for i, chunk in enumerate(chunks, start=1):
            filename = chunk.get("filename") or "unknown"
            text = chunk.get("text") or ""
            lines.append(f"### Excerpt {i} ({filename})")
            lines.append("")
            lines.append(text.strip())
            lines.append("")

    discovery = (state.get("discovery_md") or "").strip()
    lines.append("## Web discovery research (Tavily)")
    lines.append("")
    if discovery:
        lines.append(
            "Use this research for setting authenticity, character texture, "
            "and reference tone. Keep research notes as-is (usually English). "
            "Do not copy verbatim — adapt into the script language for dialogue/narration only."
        )
        lines.append("")
        lines.append(discovery)
        lines.append("")
    else:
        lines.append("_No web discovery available for this run._")
        lines.append("")

    source_md = "\n".join(lines).strip() + "\n"
    out = runs_dir(state["project_id"], state["run_id"]) / "source.md"
    out.write_text(source_md, encoding="utf-8")
    return {"source_md": source_md}
