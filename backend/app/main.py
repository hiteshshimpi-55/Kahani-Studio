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
from app.integrations.redis.client import close_redis_pool, create_redis_pool

# Import all models so SQLAlchemy metadata picks them up for create_all
import app.repository.models.audience  # noqa: F401
import app.repository.models.extraction  # noqa: F401
import app.repository.models.health  # noqa: F401
import app.repository.models.project  # noqa: F401
import app.repository.models.series  # noqa: F401
import app.repository.models.visual  # noqa: F401

log = logging.getLogger(__name__)


async def _ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("ALTER TABLE project_runs ADD COLUMN IF NOT EXISTS session_id VARCHAR(36)")
        )
        await conn.execute(
            text("ALTER TABLE sim_runs ADD COLUMN IF NOT EXISTS project_id VARCHAR(36)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_sim_runs_project_id ON sim_runs (project_id)")
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
    log.info("startup_complete", extra={"data_dir": settings.data_dir})
    yield
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
