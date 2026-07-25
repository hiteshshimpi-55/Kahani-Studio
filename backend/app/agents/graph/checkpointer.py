"""LangGraph AsyncPostgresSaver — synqed-playground pattern (pooled singleton).

Conversation history lives in checkpoint `messages` (thread_id = session_id).
No separate chat_turns table is used for message persistence.
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings

log = logging.getLogger(__name__)

_state: dict[str, Any] = {}


def psycopg_dsn() -> str:
    url = (settings.database_url or "").strip()
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgres+asyncpg://", "postgresql://")
    url = url.replace("postgresql+psycopg://", "postgresql://")
    url = url.replace("ssl=require", "sslmode=require")
    url = url.replace("ssl=true", "sslmode=require")
    return url


def get_checkpointer() -> AsyncPostgresSaver:
    cp = _state.get("checkpointer")
    if cp is None:
        raise RuntimeError("checkpointer not initialized — call init_checkpointer() at startup")
    return cp


async def init_checkpointer() -> AsyncPostgresSaver:
    if _state.get("checkpointer") is not None:
        return _state["checkpointer"]

    pool = AsyncConnectionPool(
        conninfo=psycopg_dsn(),
        max_size=10,
        open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        check=AsyncConnectionPool.check_connection,
    )
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    _state["checkpointer"] = checkpointer
    _state["pool"] = pool
    log.info("langgraph_checkpointer_ready")
    return checkpointer


async def shutdown_checkpointer() -> None:
    pool = _state.pop("pool", None)
    _state.pop("checkpointer", None)
    if pool is not None:
        await pool.close()


# Back-compat aliases used by generation graph
async def ensure_checkpoint_tables() -> None:
    await init_checkpointer()
