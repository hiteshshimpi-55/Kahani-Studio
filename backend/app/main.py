from contextlib import asynccontextmanager
from pathlib import Path
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import error_handlers
from app.api.router import router as api_router
from app.core.config import settings
from app.core.db.session import Base, engine
from app.core.logging import configure_logging
from app.integrations.redis.client import close_redis_pool, create_redis_pool
from app.middleware import logging as logging_mw
from app.middleware import request_id as request_id_mw
from app.repository import models as _models  # noqa: F401 — register ORM models
from routes.crawl import router as crawl_router
from routes.extraction import router as extraction_router

configure_logging()
log = logging.getLogger(__name__)


async def _ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE project_runs "
                "ADD COLUMN IF NOT EXISTS session_id VARCHAR(36)"
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
    app.state.redis = await create_redis_pool()
    yield
    await close_redis_pool(app.state.redis)
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

error_handlers.install(app)
# Starlette: last add_middleware is outermost — request_id must wrap access log.
logging_mw.install(app)
request_id_mw.install(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extraction_router)
app.include_router(crawl_router)
app.include_router(api_router, prefix=settings.api_prefix)
