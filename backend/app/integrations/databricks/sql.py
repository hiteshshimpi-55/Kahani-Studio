"""Unity Catalog SQL helpers via Databricks SQL Statement Execution API."""

from __future__ import annotations

import logging
import time
from typing import Any

from databricks.sdk.service.sql import StatementState

from app.core.config import settings
from app.errors.constants import ERROR_CODE_INTERNAL, ERROR_MSG_INTERNAL
from app.errors.exceptions import AppError
from app.integrations.databricks.client import get_workspace_client

log = logging.getLogger(__name__)

_POLL_SECONDS = 1.5
_POLL_TIMEOUT = 180


def resolve_warehouse_id() -> str:
    configured = (settings.databricks_sql_warehouse_id or "").strip()
    if configured:
        return configured

    w = get_workspace_client()
    warehouses = list(w.warehouses.list() or [])
    if not warehouses:
        raise AppError(
            code=ERROR_CODE_INTERNAL,
            message="No SQL warehouse found in Databricks workspace",
            http_status_code=503,
            details=["Create or start the Free Edition serverless SQL warehouse"],
        )

    # Prefer running / started warehouses, else first.
    for wh in warehouses:
        state = str(getattr(wh, "state", "") or "").upper()
        if "RUNNING" in state:
            return wh.id
    return warehouses[0].id


def execute_sql(statement: str, *, warehouse_id: str | None = None) -> dict[str, Any]:
    """Run a SQL statement and wait for completion."""
    w = get_workspace_client()
    wh_id = warehouse_id or resolve_warehouse_id()
    try:
        # Ensure warehouse is started (best-effort).
        try:
            w.warehouses.start(id=wh_id)
        except Exception:
            log.debug("warehouse_start_skipped", exc_info=True)

        response = w.statement_execution.execute_statement(
            warehouse_id=wh_id,
            statement=statement,
            wait_timeout="50s",
        )
        status = response.status
        state = status.state if status else None
        deadline = time.time() + _POLL_TIMEOUT
        while state in (StatementState.PENDING, StatementState.RUNNING):
            if time.time() > deadline:
                raise AppError(
                    code=ERROR_CODE_INTERNAL,
                    message="Databricks SQL statement timed out",
                    http_status_code=504,
                )
            time.sleep(_POLL_SECONDS)
            response = w.statement_execution.get_statement(response.statement_id)
            status = response.status
            state = status.state if status else None

        if state != StatementState.SUCCEEDED:
            err = None
            if status and status.error:
                err = getattr(status.error, "message", None) or str(status.error)
            raise AppError(
                code=ERROR_CODE_INTERNAL,
                message=ERROR_MSG_INTERNAL,
                http_status_code=502,
                details=[f"SQL failed: {err or state}"],
            )

        return {
            "statement_id": response.statement_id,
            "manifest": response.manifest.as_dict() if response.manifest else None,
            "result": response.result.as_dict() if response.result else None,
        }
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            code=ERROR_CODE_INTERNAL,
            message="Databricks SQL execution failed",
            http_status_code=502,
            details=[str(exc)],
        ) from exc


def ensure_cast_schema_and_table() -> str:
    """Create catalog.schema.cast_assets with CDF enabled. Returns table FQN."""
    catalog = settings.databricks_catalog
    schema = settings.databricks_schema
    table = settings.databricks_cast_table
    fqn = settings.databricks_cast_table_fqn

    execute_sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
    execute_sql(
        f"""
        CREATE TABLE IF NOT EXISTS {fqn} (
          id STRING NOT NULL,
          asset_type STRING NOT NULL,
          provider STRING NOT NULL,
          provider_id STRING NOT NULL,
          name STRING,
          language STRING,
          gender STRING,
          age STRING,
          accent STRING,
          use_case STRING,
          free_users_allowed BOOLEAN,
          preview_url STRING,
          tags STRING,
          description STRING NOT NULL,
          updated_at STRING
        ) USING DELTA
        TBLPROPERTIES (delta.enableChangeDataFeed = true)
        """
    )
    # Ensure CDF if table already existed without it.
    try:
        execute_sql(
            f"ALTER TABLE {fqn} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)"
        )
    except AppError:
        log.warning("cdf_alter_skipped table=%s", fqn)

    return fqn


def _sql_str(value: str | None) -> str:
    if value is None:
        return "NULL"
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def _sql_bool(value: bool | None) -> str:
    if value is None:
        return "NULL"
    return "true" if value else "false"


def clear_cast_assets() -> None:
    """Delete every row so stale curated / wrong voice IDs cannot pollute casting."""
    fqn = settings.databricks_cast_table_fqn
    execute_sql(f"DELETE FROM {fqn}")
    log.info("cast_assets_cleared table=%s", fqn)


def upsert_cast_assets(rows: list[dict[str, Any]], *, skip_per_batch_delete: bool = False) -> int:
    """Insert cast asset rows in batches. Optionally skip per-batch DELETE (after a full clear)."""
    if not rows:
        return 0
    fqn = settings.databricks_cast_table_fqn
    # Batch to keep statements manageable (SQL warehouse payload limits).
    batch_size = 50
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        if not skip_per_batch_delete:
            ids = ", ".join(_sql_str(r["id"]) for r in batch)
            execute_sql(f"DELETE FROM {fqn} WHERE id IN ({ids})")
        values_sql = []
        for r in batch:
            values_sql.append(
                "("
                + ", ".join(
                    [
                        _sql_str(r.get("id")),
                        _sql_str(r.get("asset_type")),
                        _sql_str(r.get("provider")),
                        _sql_str(r.get("provider_id")),
                        _sql_str(r.get("name")),
                        _sql_str(r.get("language")),
                        _sql_str(r.get("gender")),
                        _sql_str(r.get("age")),
                        _sql_str(r.get("accent")),
                        _sql_str(r.get("use_case")),
                        _sql_bool(r.get("free_users_allowed")),
                        _sql_str(r.get("preview_url")),
                        _sql_str(r.get("tags")),
                        _sql_str(r.get("description")),
                        _sql_str(r.get("updated_at")),
                    ]
                )
                + ")"
            )
        execute_sql(
            f"""
            INSERT INTO {fqn} (
              id, asset_type, provider, provider_id, name, language, gender, age,
              accent, use_case, free_users_allowed, preview_url, tags, description, updated_at
            ) VALUES {", ".join(values_sql)}
            """
        )
        total += len(batch)
        if total % 500 == 0 or total == len(rows):
            log.info("cast_assets_upsert_progress %s/%s", total, len(rows))
    return total


def replace_cast_assets(rows: list[dict[str, Any]]) -> int:
    """Full table replace: clear then insert. Guarantees no stale voice IDs remain."""
    clear_cast_assets()
    return upsert_cast_assets(rows, skip_per_batch_delete=True)
