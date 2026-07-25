import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.repository.models.extraction import AudioContext as AudioContextORM
from app.repository.models.extraction import ExtractionResult as ExtractionResultORM
from app.repository.models.extraction import VideoContext as VideoContextORM
from app.schemas.extraction.request import ExtractRequest
from app.schemas.extraction.response import ExtractionResponse
from contentExtraction.extraction import extract_content
from contentExtraction.markdown import to_markdown
from contentExtraction.scrapper import crawl_for_extraction

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extraction", tags=["extraction"])


@router.post("", response_class=Response)
async def extract(body: ExtractRequest, db: AsyncSession = Depends(get_db)):
    """
    1. Extract structured content from the prompt using OpenAI.
    2. Crawl the web for reference material using Tavily.
    3. Persist extraction to the database.
    4. Return a combined Markdown document.
    """
    if not body.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt must not be empty")

    log.info("extraction_start prompt=%r", body.prompt[:80])

    # ── Step 1: Extract with OpenAI ──────────────────────────────────────────
    try:
        result: ExtractionResponse = extract_content(body.prompt)
        log.info(
            "extraction_complete topic=%r characters=%d has_plot=%s",
            result.topic,
            len(result.characters),
            result.plot is not None,
        )
    except Exception:
        log.exception("extraction_failed")
        raise HTTPException(status_code=500, detail="OpenAI extraction failed")

    # ── Step 2: Crawl the web with Tavily ───────────────────────────────────
    crawl = None
    try:
        log.info("crawl_start topic=%r", result.topic)
        crawl = crawl_for_extraction(result)
        log.info(
            "crawl_complete similar_works=%d sources=%d",
            len(crawl.similar_works),
            len(crawl.all_sources),
        )
    except Exception:
        log.exception("crawl_failed — continuing without web research")

    # ── Step 3: Persist to DB ────────────────────────────────────────────────
    try:
        log.info("db_persist_start")
        video_row = VideoContextORM(
            scenes=result.video.scenes,
            objects=result.video.objects,
            colors=result.video.colors,
            style=result.video.style,
            lighting=result.video.lighting,
            camera_motion=result.video.camera_motion,
        )
        audio_row = AudioContextORM(
            genre=result.audio.genre,
            tempo=result.audio.tempo,
            instruments=result.audio.instruments,
            mood=result.audio.mood,
            sound_effects=result.audio.sound_effects,
        )
        db.add(video_row)
        db.add(audio_row)
        await db.flush()

        extraction_row = ExtractionResultORM(
            prompt=body.prompt,
            topic=result.topic,
            theme=result.theme,
            narrative=result.narrative,
            emotional_tone=result.emotional_tone,
            setting=result.setting,
            characters=[c.model_dump() for c in result.characters],
            plot=result.plot.model_dump() if result.plot else None,
            action_keywords=result.action_keywords,
            keywords=result.keywords,
            content_warnings=result.content_warnings,
            video_id=video_row.id,
            audio_id=audio_row.id,
        )
        db.add(extraction_row)
        await db.commit()
        log.info("db_persist_complete extraction_id=%d", extraction_row.id)
    except Exception:
        log.exception("db_persist_failed — returning markdown without saving")

    # ── Step 4: Return combined Markdown ─────────────────────────────────────
    md_content = to_markdown(result, crawl)
    filename = result.topic.lower().replace(" ", "_")[:40] + ".md"
    log.info("response_ready filename=%r bytes=%d", filename, len(md_content))

    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
