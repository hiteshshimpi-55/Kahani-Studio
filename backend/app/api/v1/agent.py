from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.config import settings
from app.schemas.agent.request import StartAgentRenderRequest
from app.schemas.agent.response import (
    AgentRenderResponse,
    AgentRenderStartResponse,
    McpToolsCatalogResponse,
)
from app.services.agent_render.catalog import MCP_TOOLS
from app.services.agent_render.service import AgentRenderService

router = APIRouter(prefix="/agent", tags=["agent"])


def _service(request: Request, db: AsyncSession) -> AgentRenderService:
    return AgentRenderService(db, redis=getattr(request.app.state, "redis", None))


def _public_mcp_url() -> str:
    if (settings.mcp_public_url or "").strip():
        url = settings.mcp_public_url.strip()
    else:
        base = (settings.public_api_base_url or "").rstrip("/")
        url = f"{base}/mcp" if base else "http://localhost:8000/mcp"
    # Starlette Mount redirects /mcp → /mcp/; clients should use the trailing slash.
    return url if url.endswith("/") else f"{url}/"


@router.post("/renders", response_model=AgentRenderStartResponse)
async def start_agent_render(
    body: StartAgentRenderRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AgentRenderStartResponse:
    return await _service(request, db).start_render(body)


@router.get("/renders/{job_id}", response_model=AgentRenderResponse)
async def get_agent_render(
    job_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AgentRenderResponse:
    return await _service(request, db).get_render(job_id)


@router.get("/mcp/tools", response_model=McpToolsCatalogResponse)
async def list_mcp_tools() -> McpToolsCatalogResponse:
    return McpToolsCatalogResponse(mcp_url=_public_mcp_url(), tools=MCP_TOOLS)
