from fastapi import APIRouter

from app.api.v1 import (
    audiobook,
    audience,
    cast,
    crawl,
    extraction,
    jobs,
    projects,
    search,
    timeline,
    tts,
    visuals,
)

router = APIRouter(prefix="/v1")
router.include_router(jobs.router)
router.include_router(projects.router)
router.include_router(tts.router)
router.include_router(cast.router)
router.include_router(audiobook.router)
router.include_router(search.router)
router.include_router(extraction.router)
router.include_router(crawl.router)
router.include_router(audience.router)
router.include_router(timeline.router)
router.include_router(visuals.router)
