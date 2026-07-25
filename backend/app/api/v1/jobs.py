from fastapi import APIRouter, Request

from app.services.jobs.service import JobsService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/ping")
async def enqueue_ping(request: Request):
    service = JobsService(request.app.state.redis)
    return await service.enqueue_ping()
