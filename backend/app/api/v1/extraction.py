import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.schemas.extraction.request import ExtractRequest
from app.services.extraction import service as extraction_service
from app.services.extraction.markdown import to_markdown

log = logging.getLogger(__name__)

router = APIRouter(prefix="/extraction", tags=["extraction"])


@router.post("", response_class=Response)
async def extract(body: ExtractRequest, db: AsyncSession = Depends(get_db)):
    if not body.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt must not be empty")

    log.info("extraction_start prompt=%r", body.prompt[:80])

    try:
        result, crawl = await extraction_service.extract_and_persist(body.prompt, db)
    except Exception:
        log.exception("extraction_failed")
        raise HTTPException(status_code=500, detail="OpenAI extraction failed")

    md_content = to_markdown(result, crawl)
    filename = result.topic.lower().replace(" ", "_")[:40] + ".md"
    log.info("response_ready filename=%r bytes=%d", filename, len(md_content))

    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
