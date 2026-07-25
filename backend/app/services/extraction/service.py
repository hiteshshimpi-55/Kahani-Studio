import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.llm.extraction import extract_content
from app.integrations.tavily.client import crawl_for_extraction
from app.repository.models.extraction import (
    AudioContext as AudioContextORM,
    ExtractionResult as ExtractionResultORM,
    VideoContext as VideoContextORM,
)
from app.schemas.crawl.response import CrawlResponse
from app.schemas.extraction.response import ExtractionResponse

log = logging.getLogger(__name__)


async def extract_and_persist(
    prompt: str, db: AsyncSession
) -> tuple[ExtractionResponse, CrawlResponse | None]:
    result: ExtractionResponse = extract_content(prompt)
    log.info(
        "extraction_complete topic=%r characters=%d has_plot=%s",
        result.topic,
        len(result.characters),
        result.plot is not None,
    )

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

    try:
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
            prompt=prompt,
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
        log.exception("db_persist_failed — returning result without saving")

    return result, crawl


async def get_extraction_by_id(
    extraction_id: int, db: AsyncSession
) -> ExtractionResultORM | None:
    return await db.get(ExtractionResultORM, extraction_id)
