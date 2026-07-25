"""Shot-template retrieval for the Visual Director (RAG over film grammar)."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.integrations.visuals.shot_catalog import SHOT_TEMPLATES, local_template_search

log = logging.getLogger(__name__)

_COLUMNS = [
    "id",
    "asset_type",
    "provider_id",
    "name",
    "description",
    "tags",
    "use_case",
]


def retrieve_shot_templates(query: str, *, num_results: int = 6) -> list[dict[str, Any]]:
    """ANN search for asset_type=shot_template; falls back to local catalog."""
    try:
        from app.integrations.databricks.vector_search import VectorSearchQuery, similarity_search

        result = similarity_search(
            VectorSearchQuery(
                query_text=query,
                columns=_COLUMNS,
                num_results=num_results,
                filters={"asset_type": "shot_template"},
                query_type="ANN",
                endpoint_name=settings.databricks_vector_search_endpoint,
                index_name=settings.databricks_cast_index_fqn,
            )
        )
        out: list[dict[str, Any]] = []
        for hit in result.hits:
            raw = dict(hit.raw)
            slug = (raw.get("provider_id") or "").strip()
            local = next((t for t in SHOT_TEMPLATES if t["slug"] == slug), None)
            if local:
                out.append({**local, "score": raw.get("score"), "source": "vector"})
            else:
                out.append(
                    {
                        "slug": slug or raw.get("id"),
                        "name": raw.get("name"),
                        "shot_size": raw.get("use_case") or "medium",
                        "camera_motion": "static",
                        "min_chars": 0,
                        "max_chars": 3,
                        "tags": raw.get("tags") or "",
                        "when": "",
                        "composition": raw.get("description") or "",
                        "score": raw.get("score"),
                        "source": "vector",
                    }
                )
        if out:
            log.info("shot_templates_vector hits=%d query=%s", len(out), query[:80])
            return out[:num_results]
    except Exception:
        log.warning("shot_templates_vector_failed — using local catalog", exc_info=True)

    local = local_template_search(query, num_results=num_results)
    log.info("shot_templates_local hits=%d query=%s", len(local), query[:80])
    return [dict(t, source="local") for t in local]
