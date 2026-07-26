"""Shared runtime handles for MCP tools (redis from API lifespan)."""

from __future__ import annotations

from arq.connections import ArqRedis

_redis: ArqRedis | None = None


def set_mcp_redis(redis: ArqRedis | None) -> None:
    global _redis
    _redis = redis


def get_mcp_redis() -> ArqRedis | None:
    return _redis
