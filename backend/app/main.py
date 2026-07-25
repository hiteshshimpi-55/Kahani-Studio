from contextlib import asynccontextmanager
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import Base, engine, get_db
from app.models import HealthPing
from routes.extraction import router as extraction_router


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.redis = await create_pool(redis_settings())
    yield
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(title="Kissa API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
