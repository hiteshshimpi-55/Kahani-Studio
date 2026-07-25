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


def build_source(state: ProjectGraphState) -> dict[str, Any]:
    lines = [
        "# Generation brief",
        "",
        "## User prompt",
        "",
        state["prompt"].strip(),
        "",
        "## Retrieved context",
        "",
    ]
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

    source_md = "\n".join(lines).strip() + "\n"
    out = runs_dir(state["project_id"], state["run_id"]) / "source.md"
    out.write_text(source_md, encoding="utf-8")
    return {"source_md": source_md}
