"""Static MCP tool catalog for the /mcp UI and GET /api/v1/agent/mcp/tools."""

from __future__ import annotations

from app.schemas.agent.response import McpToolCatalogItem

MCP_TOOLS: list[McpToolCatalogItem] = [
    McpToolCatalogItem(
        name="kahani_render_episode",
        description=(
            "Start a Kahani headless production job: script + narration mix for a short "
            "serial episode. Returns a job_id immediately — poll kahani_get_render until done."
        ),
        arguments=[
            {
                "name": "prompt",
                "type": "string",
                "required": True,
                "description": "Story brief or episode prompt",
            },
            {
                "name": "language",
                "type": "string",
                "required": False,
                "description": "hi or en (default hi)",
            },
            {
                "name": "title",
                "type": "string",
                "required": False,
                "description": "Optional episode title",
            },
        ],
    ),
    McpToolCatalogItem(
        name="kahani_get_render",
        description=(
            "Poll a render job. When status is done, returns audio_url plus metadata "
            "(never raw audio bytes)."
        ),
        arguments=[
            {
                "name": "job_id",
                "type": "string",
                "required": True,
                "description": "Job id from kahani_render_episode",
            },
        ],
    ),
    McpToolCatalogItem(
        name="kahani_discover_hooks",
        description=(
            "Research a topic and return ranked story hooks / plot pitch cards for "
            "Pocket FM–style serials."
        ),
        arguments=[
            {
                "name": "topic",
                "type": "string",
                "required": True,
                "description": "Topic, trend, or news hook to explore",
            },
        ],
    ),
]
