from arq.connections import ArqRedis

from app.schemas.jobs.response import EnqueuePingResponse


class JobsService:
    def __init__(self, redis: ArqRedis) -> None:
        self._redis = redis

    async def enqueue_ping(self) -> EnqueuePingResponse:
        job = await self._redis.enqueue_job("ping_job")
        return EnqueuePingResponse(
            job_id=job.job_id if job else None,
            queued=True,
        )
