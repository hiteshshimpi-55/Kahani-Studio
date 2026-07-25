import logging
from contextlib import asynccontextmanager
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import error_handlers
from app.api.router import router
from app.core.config import settings
from app.core.db.session import Base, engine

# Import all models so SQLAlchemy metadata picks them up for create_all
import app.repository.models.health  # noqa: F401
import app.repository.models.audience  # noqa: F401

log = logging.getLogger(__name__)


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Additive migrations: columns added after initial table creation
        from sqlalchemy import text
        await conn.execute(
            text("ALTER TABLE sim_runs ADD COLUMN IF NOT EXISTS project_id VARCHAR(36)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_sim_runs_project_id ON sim_runs (project_id)")
        )
    app.state.redis = await create_pool(_redis_settings())
    log.info("startup_complete", extra={"data_dir": settings.data_dir})
    yield
    await app.state.redis.aclose()
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
