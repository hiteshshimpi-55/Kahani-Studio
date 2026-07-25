"""AI Search (Vector Search) index create / sync / wait helpers."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.config import settings
from app.errors.constants import ERROR_CODE_INTERNAL, ERROR_MSG_INTERNAL
from app.errors.exceptions import AppError
from app.integrations.databricks.client import get_ai_search_client

log = logging.getLogger(__name__)

COLUMNS_TO_SYNC = [
    "id",
    "asset_type",
    "provider",
    "provider_id",
    "name",
    "language",
    "gender",
    "age",
    "accent",
    "use_case",
    "free_users_allowed",
    "preview_url",
    "description",
    "tags",
]

_EMBEDDING_FALLBACKS = (
    "databricks-qwen3-embedding-0-6b",
    "databricks-gte-large-en",
)


def _endpoint_name() -> str:
    name = (settings.databricks_vector_search_endpoint or "").strip()
    if not name:
        raise AppError(
            code=ERROR_CODE_INTERNAL,
            message="DATABRICKS_VECTOR_SEARCH_ENDPOINT is not set",
            http_status_code=503,
        )
    return name


def _index_name() -> str:
    return settings.databricks_cast_index_fqn


def _source_table() -> str:
    return settings.databricks_cast_table_fqn


def index_exists() -> bool:
    client = get_ai_search_client()
    try:
        client.get_index(endpoint_name=_endpoint_name(), index_name=_index_name())
        return True
    except Exception:
        return False


def describe_index() -> dict[str, Any]:
    client = get_ai_search_client()
    index = client.get_index(endpoint_name=_endpoint_name(), index_name=_index_name())
    desc = index.describe()
    return desc if isinstance(desc, dict) else {"raw": str(desc)}


def create_or_get_cast_index() -> Any:
    """Create Delta Sync index on cast_assets, or return existing."""
    client = get_ai_search_client()
    endpoint = _endpoint_name()
    index_name = _index_name()
    source = _source_table()

    if index_exists():
        log.info("cast_index_exists index=%s", index_name)
        return client.get_index(endpoint_name=endpoint, index_name=index_name)

    models = []
    primary = (settings.databricks_embedding_endpoint or "").strip()
    if primary:
        models.append(primary)
    for m in _EMBEDDING_FALLBACKS:
        if m not in models:
            models.append(m)

    last_error: Exception | None = None
    for model in models:
        try:
            log.info(
                "creating_cast_index index=%s source=%s model=%s",
                index_name,
                source,
                model,
            )
            index = client.create_delta_sync_index(
                endpoint_name=endpoint,
                source_table_name=source,
                index_name=index_name,
                pipeline_type="TRIGGERED",
                primary_key="id",
                embedding_source_column="description",
                embedding_model_endpoint_name=model,
                columns_to_sync=COLUMNS_TO_SYNC,
            )
            return index
        except Exception as exc:
            last_error = exc
            log.warning("create_index_failed model=%s err=%s", model, exc)

    raise AppError(
        code=ERROR_CODE_INTERNAL,
        message=ERROR_MSG_INTERNAL,
        http_status_code=502,
        details=[f"Failed to create AI Search index: {last_error}"],
    )


def sync_cast_index() -> Any:
    client = get_ai_search_client()
    index = client.get_index(endpoint_name=_endpoint_name(), index_name=_index_name())
    try:
        index.sync()
    except Exception as exc:
        # Some SDK versions sync on create; treat already-syncing as ok.
        log.warning("index_sync_warning: %s", exc)
    return index


def wait_until_online(*, timeout_sec: int = 900, poll_sec: int = 10) -> dict[str, Any]:
    """Poll index describe until detailed_state starts with ONLINE."""
    deadline = time.time() + timeout_sec
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = describe_index()
        status = last.get("status") or {}
        detailed = str(status.get("detailed_state") or status.get("state") or "")
        log.info("cast_index_state=%s", detailed)
        if detailed.upper().startswith("ONLINE"):
            return last
        # Also accept READY / ONLINE_NO_PENDING_UPDATE style states.
        if "ONLINE" in detailed.upper():
            return last
        time.sleep(poll_sec)

    raise AppError(
        code=ERROR_CODE_INTERNAL,
        message="Timed out waiting for AI Search index to become ONLINE",
        http_status_code=504,
        details=[str(last.get("status"))],
    )
