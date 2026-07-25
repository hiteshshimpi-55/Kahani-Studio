from fastapi import APIRouter

from app.api.v1 import crawl, extraction, jobs, projects

router = APIRouter(prefix="/v1")
router.include_router(jobs.router)
router.include_router(projects.router)
router.include_router(extraction.router)
router.include_router(crawl.router)
