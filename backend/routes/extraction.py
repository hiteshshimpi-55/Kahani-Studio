from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import AudioContext as AudioContextORM
from app.models import ExtractionResult as ExtractionResultORM
from app.models import VideoContext as VideoContextORM
from contentExtraction.extraction import ExtractionResult, extract_content

router = APIRouter(prefix="/api/extraction", tags=["extraction"])


class ExtractRequest(BaseModel):
    prompt: str


@router.post("", response_model=ExtractionResult)
async def extract(body: ExtractRequest, db: AsyncSession = Depends(get_db)):
    """
    Extract structured video and audio context from a user prompt
    and persist the result to the database.
    """
    if not body.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt must not be empty")

    result = extract_content(body.prompt)

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
        theme=result.theme,
        narrative=result.narrative,
        emotional_tone=result.emotional_tone,
        setting=result.setting,
        characters=result.characters,
        action_keywords=result.action_keywords,
        keywords=result.keywords,
        content_warnings=result.content_warnings,
        video_id=video_row.id,
        audio_id=audio_row.id,
    )
    db.add(extraction_row)
    await db.commit()

    return result
