"""Kahani MCP server — Streamable HTTP tools for agent-callable episode audio."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.core.db.session import AsyncSessionLocal
from app.errors import AppError
from app.mcp.runtime import get_mcp_redis
from app.schemas.agent.request import StartAgentRenderRequest
from app.services.agent_render.service import AgentRenderService

logger = logging.getLogger(__name__)

# Cursor / Claude often send Host/Origin that fail the SDK default allowlist
# (transport_security=None → empty hosts + protection on → "Invalid Host header").
# Off for local hackathon MCP; tighten before any public deploy.
_MCP_TRANSPORT_SECURITY = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
)

mcp = FastMCP(
    "Kahani",
    instructions=(
        "Kahani produces Pocket FM–style serial episode audio. "
        "Use kahani_render_episode to start a job, then poll kahani_get_render "
        "until status is done. The result includes audio_url — never raw bytes."
    ),
    stateless_http=True,
    # Mounted at FastAPI /mcp — keep streamable path at app root so URL is /mcp not /mcp/mcp.
    streamable_http_path="/",
    transport_security=_MCP_TRANSPORT_SECURITY,
)


async def _with_render_service(fn):
    redis = get_mcp_redis()
    async with AsyncSessionLocal() as session:
        try:
            svc = AgentRenderService(session, redis=redis)
            result = await fn(svc)
            await session.commit()
            return result
        except AppError:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise


@mcp.tool(
    name="kahani_render_episode",
    description=(
        "Start a Kahani headless production job (script + narration mix). "
        "Returns job_id immediately. Poll kahani_get_render until done."
    ),
)
async def kahani_render_episode(
    prompt: str,
    language: Literal["hi", "en"] = "hi",
    title: str | None = None,
) -> str:
    async def _run(svc: AgentRenderService) -> dict[str, Any]:
        started = await svc.start_render(
            StartAgentRenderRequest(prompt=prompt, language=language, title=title)
        )
        return started.model_dump()

    try:
        payload = await _with_render_service(_run)
    except AppError as exc:
        return json.dumps(
            {"error": exc.message, "code": exc.code},
            ensure_ascii=False,
        )
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool(
    name="kahani_get_render",
    description=(
        "Poll a Kahani render job. When status is done, includes audio_url and metadata "
        "(never raw audio bytes)."
    ),
)
async def kahani_get_render(job_id: str) -> str:
    async def _run(svc: AgentRenderService) -> dict[str, Any]:
        return (await svc.get_render(job_id)).model_dump()

    try:
        payload = await _with_render_service(_run)
    except AppError as exc:
        return json.dumps(
            {"error": exc.message, "code": exc.code},
            ensure_ascii=False,
        )
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool(
    name="kahani_discover_hooks",
    description=(
        "Research a topic and return ranked story hooks / plot pitch cards for "
        "Pocket FM–style serial audio."
    ),
)
async def kahani_discover_hooks(topic: str) -> str:
    from app.services.chat.orchestrator import generate_plot_pitches

    result = await generate_plot_pitches(
        user_message=topic.strip(),
        history=[],
        attachment_count=0,
    )
    pitches = result.get("pitches") if isinstance(result, dict) else None
    reply = result.get("reply") if isinstance(result, dict) else None
    payload = {
        "topic": topic.strip(),
        "reply": reply,
        "pitches": pitches or [],
    }
    return json.dumps(payload, ensure_ascii=False)


def create_mcp_http_app():
    """ASGI app for Streamable HTTP; mount at /mcp with path='/'."""
    return mcp.streamable_http_app()
