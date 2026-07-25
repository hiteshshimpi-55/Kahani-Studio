"""SSE helpers for chat streaming."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any


def sse_event(payload: dict[str, Any]) -> dict[str, str]:
    return {"data": json.dumps(payload, ensure_ascii=False)}


async def stream_text_deltas(text: str, *, chunk_size: int = 3, delay_ms: float = 14) -> AsyncIterator[dict[str, str]]:
    """Emit typewriter-friendly text deltas."""
    if not text:
        return
    i = 0
    while i < len(text):
        chunk = text[i : i + chunk_size]
        i += chunk_size
        yield sse_event({"type": "text_delta", "delta": chunk})
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)
