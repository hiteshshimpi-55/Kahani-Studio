"""
Web research layer for the content generation pipeline.

Takes a structured ExtractionResponse and searches the internet for
reference material using Tavily, then synthesizes results with OpenAI
into a structured CrawlResponse.
"""

import logging

from tavily import TavilyClient
from openai import OpenAI

from app.core.config import settings

log = logging.getLogger(__name__)
from app.schemas.crawl.response import CrawlResponse, WebReference, CharacterResearch
from app.schemas.extraction.response import ExtractionResponse


def _tavily() -> TavilyClient:
    key = (settings.tavily_api_key or "").strip()
    if not key:
        raise RuntimeError("TAVILY_API_KEY is not set")
    return TavilyClient(api_key=key)


def _openai() -> OpenAI:
    key = settings.effective_llm_api_key
    if not key:
        raise RuntimeError("LLM_API_KEY / OPENAI_API_KEY is not set")
    return OpenAI(api_key=key)


def _build_queries(extraction: ExtractionResponse) -> dict[str, list[str]]:
    """
    Build targeted search queries from each dimension of the extraction.
    Returns a dict keyed by category with a list of query strings.
    """
    queries: dict[str, list[str]] = {
        "topic_context": [
            f"{extraction.topic} background history context",
            f"{extraction.topic} {extraction.setting}",
        ],
        "similar_works": [
            f"movies shows similar to {extraction.topic} {extraction.theme}",
            f"{extraction.genre if hasattr(extraction, 'genre') else extraction.audio.genre} "
            f"{extraction.emotional_tone} similar films music",
        ],
        "visual_references": [
            f"{extraction.video.style} {extraction.video.lighting} cinematography reference",
            f"{extraction.topic} {extraction.video.style} visual art direction",
        ],
        "audio_references": [
            f"{extraction.audio.genre} {extraction.audio.mood} music reference",
            f"{extraction.audio.genre} {' '.join(extraction.audio.instruments[:2])} soundtrack",
        ],
    }

    # One query per character
    if extraction.characters:
        queries["character_references"] = [
            f"{c.name} {c.role} character reference mythology archetype"
            for c in extraction.characters
        ]

    return queries


def _search_all(
    client: TavilyClient,
    queries: dict[str, list[str]],
) -> dict[str, list[dict]]:
    """Run all queries through Tavily and bucket results by category."""
    results: dict[str, list[dict]] = {}

    for category, query_list in queries.items():
        hits: list[dict] = []
        for query in query_list:
            log.info("tavily_search category=%r query=%r", category, query)
            try:
                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=3,
                )
                found = response.get("results", [])
                log.info("tavily_result category=%r hits=%d", category, len(found))
                hits.extend(found)
            except Exception:
                log.exception("tavily_query_failed category=%r query=%r", category, query)
        results[category] = hits

    return results


def _synthesize(
    extraction: ExtractionResponse,
    raw_results: dict[str, list[dict]],
) -> CrawlResponse:
    """Use OpenAI to synthesize raw Tavily results into a structured CrawlResponse."""
    client = _openai()

    # Build a compact context string for the model
    context_lines = [
        f"TOPIC: {extraction.topic}",
        f"THEME: {extraction.theme}",
        f"SETTING: {extraction.setting}",
        f"EMOTIONAL TONE: {extraction.emotional_tone}",
        "",
        "WEB SEARCH RESULTS:",
    ]
    for category, hits in raw_results.items():
        context_lines.append(f"\n[{category.upper()}]")
        for h in hits:
            context_lines.append(
                f"- {h.get('title', '')} | {h.get('url', '')} | {h.get('content', '')[:300]}"
            )

    prompt = (
        "You are a research analyst. Using the web search results below, "
        "build a structured research report for a multimedia content generation team.\n\n"
        + "\n".join(context_lines)
    )

    model = (settings.llm_model or settings.openai_model or "gpt-4o").strip()
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Synthesize all findings into a CrawlResponse."},
        ],
        response_format=CrawlResponse,
    )

    return completion.choices[0].message.parsed


def crawl_for_extraction(extraction: ExtractionResponse) -> CrawlResponse:
    """
    Search the web for reference material based on an ExtractionResponse.

    1. Builds targeted queries from topic, characters, video style, audio style.
    2. Runs each query through Tavily.
    3. Synthesizes all results with OpenAI into a structured CrawlResponse.
    """
    tavily = _tavily()

    queries = _build_queries(extraction)
    raw_results = _search_all(tavily, queries)
    return _synthesize(extraction, raw_results)
