import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import error_handlers
from app.api.router import router
from app.core.config import settings
from app.core.db.session import Base, engine
from app.core.logging import configure_logging
from app.integrations.redis.client import close_redis_pool, create_redis_pool
from app.mcp.runtime import set_mcp_redis
from app.mcp.server import create_mcp_http_app

configure_logging()

# Import all models so SQLAlchemy metadata picks them up for create_all
import app.repository.models.audience  # noqa: F401
import app.repository.models.extraction  # noqa: F401
import app.repository.models.health  # noqa: F401
import app.repository.models.project  # noqa: F401
import app.repository.models.series  # noqa: F401
import app.repository.models.visual  # noqa: F401

log = logging.getLogger(__name__)

mcp_http_app = create_mcp_http_app()


async def _ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE project_runs "
                "ADD COLUMN IF NOT EXISTS session_id VARCHAR(36)"
            )
        )
        await conn.execute(
            text("ALTER TABLE scripts ADD COLUMN IF NOT EXISTS part_number INTEGER")
        )
        await conn.execute(
            text(
                "ALTER TABLE scripts "
                "ADD COLUMN IF NOT EXISTS pinned BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE project_runs "
                "ADD COLUMN IF NOT EXISTS part_number INTEGER"
            )
        )
        # Staged production pipeline columns
        await conn.execute(
            text(
                "ALTER TABLE project_runs "
                "ADD COLUMN IF NOT EXISTS current_stage VARCHAR(32)"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE project_runs "
                "ADD COLUMN IF NOT EXISTS stage_statuses JSONB"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE project_runs "
                "ADD COLUMN IF NOT EXISTS audio_s3_key VARCHAR(1024)"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE project_runs "
                "ADD COLUMN IF NOT EXISTS cover_s3_key VARCHAR(1024)"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE project_runs "
                "ADD COLUMN IF NOT EXISTS manifest_s3_key VARCHAR(1024)"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE project_runs "
                "ADD COLUMN IF NOT EXISTS revision_notes TEXT"
            )
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    try:
        await _ensure_schema()
    except Exception:
        log.exception(
            "database_startup_failed — API will start; /api/health will show postgres down. "
            "Check DATABASE_URL (user:password@host) in .env"
        )
    try:
        from app.agents.graph.checkpointer import init_checkpointer

        await init_checkpointer()
    except Exception:
        log.exception(
            "langgraph_checkpoint_setup_failed — chat history / runs need Postgres checkpointer"
        )
    app.state.redis = await create_redis_pool()
    set_mcp_redis(app.state.redis)
    log.info("startup_complete", extra={"data_dir": settings.data_dir})

    # Streamable HTTP MCP requires its session-manager lifespan (mounted apps
    # do not inherit nested Starlette lifespans automatically).
    mcp_lifespan = getattr(mcp_http_app.router, "lifespan_context", None)
    if mcp_lifespan is not None:
        async with mcp_lifespan(mcp_http_app):
            yield
    else:
        yield

    set_mcp_redis(None)
    try:
        from app.agents.graph.checkpointer import shutdown_checkpointer

        await shutdown_checkpointer()
    except Exception:
        log.exception("checkpointer_shutdown_failed")
    await close_redis_pool(app.state.redis)
    await engine.dispose()


app = FastAPI(title="Kissa API", version="0.1.0", lifespan=lifespan)

error_handlers.install(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)
# Streamable HTTP MCP — copyable URL: {PUBLIC_API_BASE_URL}/mcp
app.mount("/mcp", mcp_http_app)
