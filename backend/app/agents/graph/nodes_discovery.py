"""Web discovery via Parminal's extraction + Tavily crawl — feeds script writer."""

from __future__ import annotations

import logging
from typing import Any

from app.agents.graph.state import ProjectGraphState
from app.core.config import settings
from app.services.projects.storage import run_object_prefix, runs_dir
from app.integrations.s3 import get_artifact_storage

logger = logging.getLogger(__name__)


def discover_research(state: ProjectGraphState) -> dict[str, Any]:
    """Extract structured story context and enrich with Tavily web research.

    Non-fatal: on failure returns empty discovery_md so script writing continues.
    Skips if chat already pre-researched (discovery_md already present).
    """
    existing_md = (state.get("discovery_md") or "").strip()
    if existing_md:
        logger.info(
            "discover_research_skipped — preloaded discovery_md chars=%d",
            len(existing_md),
        )
        return {}

    prompt = (state.get("prompt") or "").strip()
    project_id = state.get("project_id") or ""
    run_id = state.get("run_id") or ""
    errors = list(state.get("errors") or [])

    if not prompt:
        return {"discovery_md": "", "extraction": None, "crawl": None}

    api_key = settings.effective_llm_api_key
    if not api_key:
        logger.warning("discover_research_skipped — no LLM_API_KEY / OPENAI_API_KEY")
        return {
            "discovery_md": "",
            "extraction": None,
            "crawl": None,
            "errors": errors + ["discovery skipped: missing LLM API key"],
        }

    try:
        from app.integrations.llm.extraction import extract_content
        from app.services.extraction.markdown import to_markdown

        extraction = extract_content(prompt)
        crawl = None
        tavily_key = (settings.tavily_api_key or "").strip()
        if tavily_key:
            try:
                from app.integrations.tavily.client import crawl_for_extraction

                crawl = crawl_for_extraction(extraction)
            except Exception as exc:  # noqa: BLE001
                logger.exception("tavily_crawl_failed")
                errors.append(f"tavily crawl failed: {exc}")
        else:
            logger.warning("discover_research — TAVILY_API_KEY unset; extraction only")
            errors.append("discovery: TAVILY_API_KEY unset — extraction only")

        discovery_md = to_markdown(extraction, crawl)
        _persist_discovery(project_id, run_id, discovery_md)

        logger.info(
            "discover_research_ok topic=%r crawl=%s chars=%d",
            extraction.topic,
            crawl is not None,
            len(extraction.characters or []),
        )
        return {
            "discovery_md": discovery_md,
            "extraction": extraction.model_dump(mode="json"),
            "crawl": crawl.model_dump(mode="json") if crawl else None,
            "errors": errors,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("discover_research_failed")
        return {
            "discovery_md": "",
            "extraction": None,
            "crawl": None,
            "errors": errors + [f"discovery failed: {exc}"],
        }


def _persist_discovery(project_id: str, run_id: str, discovery_md: str) -> None:
    if not project_id or not run_id or not discovery_md.strip():
        return
    # Local working copy
    try:
        path = runs_dir(project_id, run_id) / "discovery.md"
        path.write_text(discovery_md, encoding="utf-8")
    except OSError:
        logger.exception("discovery_local_write_failed")
    # S3 / ArtifactStorage
    try:
        key = f"{run_object_prefix(project_id, run_id)}/discovery.md"
        get_artifact_storage().put_text(
            key,
            discovery_md,
            content_type="text/markdown; charset=utf-8",
        )
    except Exception:  # noqa: BLE001
        logger.exception("discovery_s3_write_failed")
