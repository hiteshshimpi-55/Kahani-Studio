from typing import Any

from pydantic import BaseModel


class HealthDependencyStatus(BaseModel):
    ok: bool
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    postgres: HealthDependencyStatus
    redis: HealthDependencyStatus
    data_dir: str


class Envelope(BaseModel):
    data: dict[str, Any]
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class HealthPing(Base):
    """Minimal table so compose can verify Postgres wiring. No product features."""

    __tablename__ = "health_pings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64), default="api")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class VideoContext(Base):
    """Visual keywords and directives extracted from a user prompt."""

    __tablename__ = "video_contexts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scenes: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    objects: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    colors: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    style: Mapped[str] = mapped_column(String(128), nullable=False)
    lighting: Mapped[str] = mapped_column(String(128), nullable=False)
    camera_motion: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    extraction: Mapped[Optional["ExtractionResult"]] = relationship(
        back_populates="video"
    )


class AudioContext(Base):
    """Audio keywords and directives extracted from a user prompt."""

    __tablename__ = "audio_contexts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    genre: Mapped[str] = mapped_column(String(128), nullable=False)
    tempo: Mapped[str] = mapped_column(String(64), nullable=False)
    instruments: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    mood: Mapped[str] = mapped_column(String(128), nullable=False)
    sound_effects: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    extraction: Mapped[Optional["ExtractionResult"]] = relationship(
        back_populates="audio"
    )


class ExtractionResult(Base):
    """Full structured content extraction produced from a user prompt."""

    __tablename__ = "extraction_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    theme: Mapped[str] = mapped_column(String(256), nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    emotional_tone: Mapped[str] = mapped_column(String(128), nullable=False)
    setting: Mapped[str] = mapped_column(String(256), nullable=False)
    characters: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    action_keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    content_warnings: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    video_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("video_contexts.id"), nullable=False
    )
    audio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("audio_contexts.id"), nullable=False
    )

    video: Mapped[VideoContext] = relationship(back_populates="extraction")
    audio: Mapped[AudioContext] = relationship(back_populates="extraction")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
