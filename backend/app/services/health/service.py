from pathlib import Path

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repository.health import health as health_repo
from app.schemas.common import HealthDependencyStatus, HealthResponse
from app.schemas.jobs.response import DbPingResponse


class HealthService:
    async def check(self, request: Request, db: AsyncSession) -> HealthResponse:
        db_ok = False
        redis_ok = False
        db_error: str | None = None
        redis_error: str | None = None

        try:
            await db.execute(text("SELECT 1"))
            db_ok = True
        except Exception as exc:  # noqa: BLE001
            db_error = str(exc)

        try:
            redis_ok = bool(await request.app.state.redis.ping())
        except Exception as exc:  # noqa: BLE001
            redis_error = str(exc)

        return HealthResponse(
            status="ok" if db_ok and redis_ok else "degraded",
            service=settings.app_name,
            postgres=HealthDependencyStatus(ok=db_ok, error=db_error),
            redis=HealthDependencyStatus(ok=redis_ok, error=redis_error),
            data_dir=settings.data_dir,
        )

    async def ping_db(self, db: AsyncSession) -> DbPingResponse:
        Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
        row = await health_repo.create_ping(db, source="api")
        return DbPingResponse(id=row.id, source=row.source)
