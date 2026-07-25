from typing import Any

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

    async def enqueue_visual_render(self, payload: dict[str, Any]) -> Any:
        return await self._redis.enqueue_job("render_visual_track", payload)
