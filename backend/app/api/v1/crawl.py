import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.integrations.tavily.client import crawl_for_extraction
from app.schemas.crawl.request import CrawlRequest
from app.schemas.crawl.response import CrawlResponse
from app.schemas.extraction.response import ExtractionResponse
from app.services.extraction import service as extraction_service

log = logging.getLogger(__name__)

router = APIRouter(prefix="/crawl", tags=["crawl"])


@router.post("", response_model=CrawlResponse)
async def crawl(body: CrawlRequest, db: AsyncSession = Depends(get_db)):
    extraction: ExtractionResponse | None = None

    if body.extraction:
        extraction = body.extraction
    elif body.extraction_id is not None:
        row = await extraction_service.get_extraction_by_id(body.extraction_id, db)
        if row is None:
            raise HTTPException(status_code=404, detail="extraction not found")

        extraction = ExtractionResponse.model_validate({
            "topic": row.topic,
            "theme": row.theme,
            "narrative": row.narrative,
            "emotional_tone": row.emotional_tone,
            "setting": row.setting,
            "characters": row.characters,
            "plot": row.plot,
            "action_keywords": row.action_keywords,
            "keywords": row.keywords,
            "content_warnings": row.content_warnings,
            "video": row.video.__dict__ if row.video else {},
            "audio": row.audio.__dict__ if row.audio else {},
        })
    else:
        raise HTTPException(
            status_code=422,
            detail="provide either extraction_id or extraction",
        )

    return crawl_for_extraction(extraction)
