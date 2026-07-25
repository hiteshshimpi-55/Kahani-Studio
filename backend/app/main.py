from contextlib import asynccontextmanager
from pathlib import Path
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import Base, engine, get_db
from app.models import HealthPing
from routes.extraction import router as extraction_router
from app.api import error_handlers
from app.api.router import router as api_router
from app.core.config import settings
from app.core.db.session import Base, engine
from app.core.logging import configure_logging
from app.integrations.redis.client import close_redis_pool, create_redis_pool
from app.middleware import logging as logging_mw
from app.middleware import request_id as request_id_mw
from app.repository import models as _models  # noqa: F401 — register ORM models

configure_logging()
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
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
@app.get("/api/health")
async def health(db: AsyncSession = Depends(get_db)):
    db_ok = False
    redis_ok = False
    db_error = None
    redis_error = None
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001 — surface status in health only
        db_error = str(exc)

    try:
        redis_ok = bool(await app.state.redis.ping())
    except Exception as exc:  # noqa: BLE001
        redis_error = str(exc)

    return {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "service": settings.app_name,
        "postgres": {"ok": db_ok, "error": db_error},
        "redis": {"ok": redis_ok, "error": redis_error},
        "data_dir": settings.data_dir,
    }


@app.post("/api/jobs/ping")
async def enqueue_ping():
    """Enqueue a no-op worker job to verify the generation queue wiring."""
    job = await app.state.redis.enqueue_job("ping_job")
    return {"job_id": job.job_id if job else None, "queued": True}


@app.post("/api/health/ping-db")
async def ping_db(db: AsyncSession = Depends(get_db)):
    row = HealthPing(source="api")
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"id": row.id, "source": row.source}

app.include_router(api_router, prefix=settings.api_prefix)

