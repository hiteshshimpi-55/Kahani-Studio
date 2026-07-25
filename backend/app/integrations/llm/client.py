"""Provider-agnostic LLM chat helper.

Configured via LLM_PROVIDER / LLM_API_KEY / LLM_MODEL.
Supported providers: openai (default), anthropic.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
}


def resolve_llm_settings() -> tuple[str, str, str]:
    provider = (settings.llm_provider or "openai").strip().lower()
    api_key = settings.effective_llm_api_key
    model = (settings.llm_model or settings.openai_model or "").strip() or DEFAULT_MODELS.get(
        provider, "gpt-4o"
    )
    return provider, api_key, model


async def chat_completion(
    *,
    messages: list[dict[str, str]],
    max_tokens: int = 4096,
    temperature: float = 0.7,
    json_mode: bool = True,
) -> str:
    """Run a single chat completion; returns assistant text."""
    provider, api_key, model = resolve_llm_settings()
    if not api_key:
        raise RuntimeError("LLM_API_KEY is not set")

    if provider == "openai":
        return await _openai_chat(
            api_key, model, messages, max_tokens, temperature, json_mode=json_mode
        )
    if provider == "anthropic":
        return await _anthropic_chat(api_key, model, messages, max_tokens, temperature)
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


async def _openai_chat(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
    *,
    json_mode: bool = True,
) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = await client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content or ""
    return content


async def _anthropic_chat(
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> str:
    import anthropic

    system = ""
    user_messages: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        if role == "system":
            system = msg.get("content") or ""
        else:
            user_messages.append({"role": role or "user", "content": msg.get("content") or ""})

    client = anthropic.AsyncAnthropic(api_key=api_key)
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": user_messages,
    }
    if system:
        kwargs["system"] = system
    msg = await client.messages.create(**kwargs)
    parts: list[str] = []
    for block in msg.content or []:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts)
