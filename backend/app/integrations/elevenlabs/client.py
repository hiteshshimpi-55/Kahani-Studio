from elevenlabs.client import AsyncElevenLabs, ElevenLabs

from app.core.config import settings
from app.errors.constants import (
    ERROR_CODE_ELEVENLABS_NOT_CONFIGURED,
    ERROR_MSG_ELEVENLABS_NOT_CONFIGURED,
)
from app.errors.exceptions import AppError


def _require_api_key() -> str:
    key = (settings.elevenlabs_api_key or "").strip()
    if not key:
        raise AppError(
            code=ERROR_CODE_ELEVENLABS_NOT_CONFIGURED,
            message=ERROR_MSG_ELEVENLABS_NOT_CONFIGURED,
            http_status_code=503,
        )
    return key


def get_elevenlabs_client() -> ElevenLabs:
    """Sync SDK client for workers / scripts."""
    return ElevenLabs(api_key=_require_api_key())


def get_async_elevenlabs_client() -> AsyncElevenLabs:
    """Async SDK client for FastAPI request paths."""
    return AsyncElevenLabs(api_key=_require_api_key())
