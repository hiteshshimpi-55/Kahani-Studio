"""Replicate image generation client."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import replicate

from app.core.config import settings
from app.errors.constants import (
    ERROR_CODE_REPLICATE_FAILED,
    ERROR_CODE_REPLICATE_NOT_CONFIGURED,
    ERROR_MSG_REPLICATE_FAILED,
    ERROR_MSG_REPLICATE_NOT_CONFIGURED,
)
from app.errors.exceptions import AppError

log = logging.getLogger(__name__)


def _require_token() -> str:
    token = (settings.replicate_api_token or "").strip()
    if not token:
        raise AppError(
            code=ERROR_CODE_REPLICATE_NOT_CONFIGURED,
            message=ERROR_MSG_REPLICATE_NOT_CONFIGURED,
            http_status_code=503,
        )
    return token


def get_replicate_client() -> replicate.Client:
    token = _require_token()
    os.environ.setdefault("REPLICATE_API_TOKEN", token)
    return replicate.Client(api_token=token)


def _first_output_url(output: Any) -> str:
    if output is None:
        raise AppError(
            code=ERROR_CODE_REPLICATE_FAILED,
            message=ERROR_MSG_REPLICATE_FAILED,
            http_status_code=502,
            details=["empty output"],
        )
    if isinstance(output, str):
        return output
    if isinstance(output, (list, tuple)) and output:
        item = output[0]
        return item if isinstance(item, str) else str(item)
    # FileOutput-like
    url = getattr(output, "url", None)
    if callable(url):
        return str(url())
    if url:
        return str(url)
    return str(output)


def download_to_path(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
    return dest


def run_model(model: str, input_payload: dict[str, Any]) -> str:
    """Run a Replicate model and return the first output URL."""
    import time

    client = get_replicate_client()
    last_exc: Exception | None = None
    for attempt in range(1, 8):
        try:
            log.info(
                "replicate_run model=%s attempt=%s keys=%s",
                model,
                attempt,
                sorted(input_payload.keys()),
            )
            # File handles must be reopened each attempt.
            payload = dict(input_payload)
            for key, value in list(payload.items()):
                if hasattr(value, "read") and hasattr(value, "seek"):
                    try:
                        value.seek(0)
                    except Exception:
                        pass
            output = client.run(model, input=payload)
            return _first_output_url(output)
        except AppError:
            raise
        except Exception as exc:
            last_exc = exc
            msg = str(exc)
            throttled = (
                "429" in msg
                or "throttled" in msg.lower()
                or "rate limit" in msg.lower()
            )
            timed_out = "timeout" in msg.lower() or "timed out" in msg.lower()
            if (throttled or timed_out) and attempt < 7:
                wait = min(20 * attempt, 90) if throttled else min(5 * attempt, 30)
                log.warning(
                    "replicate_retry attempt=%s wait=%ss reason=%s",
                    attempt,
                    wait,
                    "throttle" if throttled else "timeout",
                )
                time.sleep(wait)
                continue
            break
    raise AppError(
        code=ERROR_CODE_REPLICATE_FAILED,
        message=ERROR_MSG_REPLICATE_FAILED,
        http_status_code=502,
        details=[str(last_exc) if last_exc else "unknown"],
    ) from last_exc


def local_or_http_face_ref(path_or_url: str) -> Any:
    """PuLID accepts HTTP URLs or open file handles for local paths."""
    parsed = urlparse(path_or_url)
    if parsed.scheme in ("http", "https"):
        return path_or_url
    p = Path(path_or_url)
    if not p.is_file():
        raise AppError(
            code=ERROR_CODE_REPLICATE_FAILED,
            message=ERROR_MSG_REPLICATE_FAILED,
            http_status_code=400,
            details=[f"face ref not found: {path_or_url}"],
        )
    return open(p, "rb")
