from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.models.health import HealthPing


async def create_ping(session: AsyncSession, *, source: str = "api") -> HealthPing:
    row = HealthPing(source=source)
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row
