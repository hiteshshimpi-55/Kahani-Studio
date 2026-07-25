from databricks.ai_search.client import AISearchClient
from databricks.sdk import WorkspaceClient

from app.core.config import settings
from app.errors.constants import (
    ERROR_CODE_DATABRICKS_NOT_CONFIGURED,
    ERROR_MSG_DATABRICKS_NOT_CONFIGURED,
)
from app.errors.exceptions import AppError


def _host_and_token() -> tuple[str, str]:
    host = (settings.databricks_host or "").strip().rstrip("/")
    token = (settings.databricks_token or "").strip()
    if not host or not token:
        raise AppError(
            code=ERROR_CODE_DATABRICKS_NOT_CONFIGURED,
            message=ERROR_MSG_DATABRICKS_NOT_CONFIGURED,
            http_status_code=503,
        )
    if not host.startswith("http"):
        host = f"https://{host}"
    return host, token


def get_workspace_client() -> WorkspaceClient:
    host, token = _host_and_token()
    return WorkspaceClient(host=host, token=token)


def get_ai_search_client() -> AISearchClient:
    """AI Search client (Vector Search renamed)."""
    host, token = _host_and_token()
    return AISearchClient(
        workspace_url=host,
        personal_access_token=token,
        disable_notice=True,
    )


# Backward-compatible alias name used in older docs.
get_vector_search_client = get_ai_search_client
