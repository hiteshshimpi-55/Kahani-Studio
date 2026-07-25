from fastapi import APIRouter

from app.api.v1 import jobs

router = APIRouter(prefix="/v1")
router.include_router(jobs.router)
