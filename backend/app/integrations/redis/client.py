from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import settings


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


async def create_redis_pool() -> ArqRedis:
    return await create_pool(redis_settings())


async def close_redis_pool(pool: ArqRedis | None) -> None:
    if pool is not None:
        await pool.aclose()
