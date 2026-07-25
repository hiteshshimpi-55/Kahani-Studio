"""Tavily-backed story research for project runs.

Searches the web for content related to the story's plot and saves
research.json to the run directory.
"""

from __future__ import annotations

import asyncio
import json
import logging

from app.core.config import settings
from app.services.projects.storage import runs_dir

log = logging.getLogger(__name__)

_RESEARCH_FILE = "research.json"

_CATEGORIES = [
    ("similar_stories", "{prompt} similar stories podcast audio drama serial"),
    ("cultural_context", "{prompt} cultural background setting history"),
    ("character_archetypes", "{prompt} character archetype psychology motivation"),
    ("emotional_themes", "{prompt} emotional themes audience appeal narrative hooks"),
]


def _build_queries(prompt: str) -> list[tuple[str, str]]:
    base = prompt.strip()[:180]
    return [(cat, template.format(prompt=base)) for cat, template in _CATEGORIES]


def _search_tavily(queries: list[tuple[str, str]]) -> dict[str, list[dict]]:
    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)
    results: dict[str, list[dict]] = {}

    for category, query in queries:
        hits: list[dict] = []
        log.info("tavily_story_research category=%r query=%r", category, query)
        try:
            response = client.search(query=query, search_depth="basic", max_results=4)
            for r in response.get("results", []):
                hits.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:400],
                    "score": round(float(r.get("score", 0)), 3),
                })
            log.info("tavily_story_research category=%r hits=%d", category, len(hits))
        except Exception:
            log.exception("tavily_story_research_failed category=%r", category)
        results[category] = hits

    return results


def _do_research(project_id: str, run_id: str, prompt: str) -> dict:
    queries = _build_queries(prompt)
    results = _search_tavily(queries)
    research = {
        "project_id": project_id,
        "run_id": run_id,
        "prompt": prompt,
        "queries": {cat: q for cat, q in queries},
        "results": results,
    }
    path = runs_dir(project_id, run_id) / _RESEARCH_FILE
    path.write_text(json.dumps(research, ensure_ascii=False, indent=2), encoding="utf-8")
    return research


async def run_story_research(project_id: str, run_id: str, prompt: str) -> dict:
    """Run Tavily searches for the story, persist research.json, return the data."""
    if not settings.tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY is not configured")
    return await asyncio.to_thread(_do_research, project_id, run_id, prompt)


def read_story_research(project_id: str, run_id: str) -> dict | None:
    """Read previously saved research.json for a run."""
    path = runs_dir(project_id, run_id) / _RESEARCH_FILE
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
