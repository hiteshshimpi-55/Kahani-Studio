from fastapi import APIRouter

from app.api.v1 import jobs, projects

router = APIRouter(prefix="/v1")
router.include_router(jobs.router)
router.include_router(projects.router)
