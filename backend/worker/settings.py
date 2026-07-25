from arq.connections import RedisSettings

from app.core.config import settings
from app.workers.jobs import (
    delete_attachment_index_job,
    index_attachment_job,
    project_run_job,
)


async def ping_job(ctx: dict) -> dict:
    """Smoke-test job — proves worker + Redis queue are wired."""
    marker = f"{settings.data_dir}/worker_ping.txt"
    with open(marker, "a", encoding="utf-8") as f:
        f.write("ping\n")
    return {"ok": True, "marker": marker}


class WorkerSettings:
    functions = [
        ping_job,
        index_attachment_job,
        delete_attachment_index_job,
        project_run_job,
    ]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 5
