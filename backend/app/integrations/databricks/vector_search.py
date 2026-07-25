from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.errors.constants import (
    ERROR_CODE_VECTOR_SEARCH_FAILED,
    ERROR_CODE_VECTOR_SEARCH_NOT_CONFIGURED,
    ERROR_MSG_VECTOR_SEARCH_FAILED,
    ERROR_MSG_VECTOR_SEARCH_NOT_CONFIGURED,
)
from app.errors.exceptions import AppError
from app.integrations.databricks.client import get_ai_search_client
from app.integrations.databricks.constants import DEFAULT_NUM_RESULTS, DEFAULT_QUERY_TYPE


@dataclass(frozen=True, slots=True)
class VectorSearchQuery:
    query_text: str
    columns: list[str] | None = None
    num_results: int = DEFAULT_NUM_RESULTS
    filters: dict[str, Any] | str | None = None
    query_type: str = DEFAULT_QUERY_TYPE
    endpoint_name: str | None = None
    index_name: str | None = None


@dataclass(frozen=True, slots=True)
class VectorSearchHit:
    raw: dict[str, Any]


@dataclass(frozen=True, slots=True)
class VectorSearchResult:
    endpoint_name: str
    index_name: str
    hits: list[VectorSearchHit]
    raw: dict[str, Any]


def _configured_endpoint_and_index(
    endpoint_name: str | None,
    index_name: str | None,
) -> tuple[str, str]:
    endpoint = (endpoint_name or settings.databricks_vector_search_endpoint or "").strip()
    index = (index_name or settings.databricks_vector_search_index or "").strip()
    if not endpoint or not index:
        raise AppError(
            code=ERROR_CODE_VECTOR_SEARCH_NOT_CONFIGURED,
            message=ERROR_MSG_VECTOR_SEARCH_NOT_CONFIGURED,
            http_status_code=503,
        )
    return endpoint, index


def _default_columns(columns: list[str] | None) -> list[str]:
    if columns:
        return columns
    raw = settings.databricks_vector_search_columns or "id,text"
    return [c.strip() for c in raw.split(",") if c.strip()]


def _normalize_hits(payload: Any) -> tuple[list[VectorSearchHit], dict[str, Any]]:
    if payload is None:
        return [], {}
    if isinstance(payload, dict):
        data = payload
    elif hasattr(payload, "as_dict"):
        data = payload.as_dict()
    elif hasattr(payload, "to_dict"):
        data = payload.to_dict()
    else:
        data = {"result": payload}

    result_block = data.get("result") if isinstance(data, dict) else None
    rows: list[Any] = []
    if isinstance(result_block, dict):
        rows = result_block.get("data_array") or result_block.get("data") or []
        col_names = (
            result_block.get("column_names")
            or (data.get("manifest") or {}).get("columns")
            or result_block.get("manifest", {}).get("columns")
        )
        if rows and col_names and isinstance(rows[0], (list, tuple)):
            names = [
                c["name"] if isinstance(c, dict) else str(c) for c in col_names
            ]
            hits: list[VectorSearchHit] = []
            for row in rows:
                raw = {names[i]: row[i] for i in range(min(len(names), len(row)))}
                # Score is often appended after named columns.
                if len(row) > len(names):
                    raw["score"] = row[-1]
                elif "score" not in raw and len(row) == len(names) + 0:
                    pass
                hits.append(VectorSearchHit(raw=raw))
            return hits, data
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return [VectorSearchHit(raw=row) for row in rows], data
    if isinstance(data.get("data"), list):
        return [VectorSearchHit(raw=row if isinstance(row, dict) else {"value": row}) for row in data["data"]], data
    return [VectorSearchHit(raw={"value": data})], data if isinstance(data, dict) else {"result": data}


def similarity_search(query: VectorSearchQuery) -> VectorSearchResult:
    """Run ANN / hybrid query against the configured AI Search index."""
    endpoint, index_name = _configured_endpoint_and_index(
        query.endpoint_name,
        query.index_name,
    )
    client = get_ai_search_client()
    try:
        index = client.get_index(endpoint_name=endpoint, index_name=index_name)
        payload = index.similarity_search(
            columns=_default_columns(query.columns),
            query_text=query.query_text,
            filters=query.filters,
            num_results=query.num_results,
            query_type=query.query_type,
        )
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            code=ERROR_CODE_VECTOR_SEARCH_FAILED,
            message=ERROR_MSG_VECTOR_SEARCH_FAILED,
            http_status_code=502,
            details=[str(exc)],
        ) from exc

    hits, raw = _normalize_hits(payload)
    return VectorSearchResult(
        endpoint_name=endpoint,
        index_name=index_name,
        hits=hits,
        raw=raw,
    )
