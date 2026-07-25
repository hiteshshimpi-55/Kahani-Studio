"""Discover service: Tavily-scraped regional content → LLM story topics."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

from app.core.config import settings
from app.integrations.llm.client import chat_completion
from app.schemas.discover.response import TopicCard, TrendingTopicsResponse

log = logging.getLogger(__name__)

REGION_NAMES: dict[str, str] = {
    "IN": "India",
    "US": "United States",
    "UK": "United Kingdom",
    "PK": "Pakistan",
    "NG": "Nigeria",
    "AU": "Australia",
    "CA": "Canada",
    "ZA": "South Africa",
    "BD": "Bangladesh",
    "PH": "Philippines",
}

_SYSTEM = """\
You are a content trends analyst specialising in audio drama and podcast storytelling.
Your job is to surface story concepts that are culturally resonant, emotionally compelling,
and grounded in real events trending in the specified region.

When given real news snippets, transform each into a fictional audio drama concept —
preserve the emotional core and cultural specificity, but reframe it as a story premise.

Return ONLY valid JSON — no prose, no markdown fences.
Schema:
{
  "topics": [
    {
      "title": "short punchy concept name (≤8 words)",
      "genre": "one of: Thriller, Romance, Drama, Horror, Comedy, Family, Crime, Mystery, Spiritual, Historical",
      "mood": "2-3 word mood (e.g. 'dark and tense')",
      "hook": "one sentence that makes a listener want to press play immediately",
      "tags": ["2-4 relevant string tags"],
      "why_trending": "one sentence explaining the real-world event or social tension this is drawn from"
    }
  ]
}
"""


def _run_tavily_query(query: str, max_results: int = 5) -> list[dict]:
    """Single synchronous Tavily search — run via asyncio.to_thread."""
    from tavily import TavilyClient
    client = TavilyClient(api_key=settings.tavily_api_key)
    try:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
        )
        return response.get("results", [])
    except Exception:
        log.exception("tavily_search_failed query=%r", query)
        return []


async def _scrape_region(location: str) -> list[dict]:
    """Run parallel Tavily searches for trending content in the location."""
    queries = [
        f"trending news {location} 2025",
        f"viral story crime romance politics {location}",
        f"social issue controversy {location} today",
    ]
    results = await asyncio.gather(
        *[asyncio.to_thread(_run_tavily_query, q) for q in queries]
    )
    merged: list[dict] = []
    for batch in results:
        merged.extend(batch)
    return merged


def _build_context_block(web_results: list[dict], cap: int = 15) -> str:
    lines = []
    for r in web_results[:cap]:
        title = (r.get("title") or "").strip()
        snippet = (r.get("content") or "")[:250].strip()
        if title or snippet:
            lines.append(f"- {title}: {snippet}")
    return "\n".join(lines)


class DiscoverService:
    async def get_trending(
        self, region: str, state: str | None = None, count: int = 8
    ) -> TrendingTopicsResponse:
        region = region.upper()
        region_name = REGION_NAMES.get(region, region)
        location = f"{state}, {region_name}" if state else region_name

        # 1. Scrape real trending content via Tavily
        web_results: list[dict] = []
        if settings.tavily_api_key:
            log.info("discover_tavily_scrape location=%r", location)
            web_results = await _scrape_region(location)
            log.info("discover_tavily_results count=%d", len(web_results))

        # 2. Build user prompt — grounded when we have real content
        if web_results:
            context = _build_context_block(web_results)
            user_prompt = (
                f"Generate {count} audio story topic cards for {location}.\n\n"
                f"Use these real trending stories and news from {location} as source material:\n"
                f"{context}\n\n"
                "For each real item, reimagine it as a fictional audio drama concept. "
                "Preserve the emotional core and local cultural specificity. "
                "Mix genres — not every topic needs to be the same genre. "
                "why_trending should cite the real event or tension you drew from."
            )
        else:
            log.warning("discover_tavily_skipped no_key_or_empty location=%r", location)
            user_prompt = (
                f"Generate {count} trending audio story topics for {location}.\n"
                "Consider current news cycles, cultural events, local politics, social tensions, "
                f"and regional storytelling traditions specific to {location}. "
                "Avoid generic concepts that could apply anywhere."
            )

        raw = await chat_completion(
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
            temperature=0.8,
            json_mode=True,
        )

        data = json.loads(raw)
        topics = [
            TopicCard(id=str(uuid.uuid4()), **t) for t in data.get("topics", [])
        ]

        return TrendingTopicsResponse(
            region=region,
            region_name=region_name,
            state=state or "",
            topics=topics,
        )
