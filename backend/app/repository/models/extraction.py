from typing import Any, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.repository.models.base.base import Base
from app.repository.models.base.mixins import TimestampMixin


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

    extraction: Mapped[Optional["ExtractionResult"]] = relationship(back_populates="video")


class AudioContext(Base):
    """Audio keywords and directives extracted from a user prompt."""

    __tablename__ = "audio_contexts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    genre: Mapped[str] = mapped_column(String(128), nullable=False)
    tempo: Mapped[str] = mapped_column(String(64), nullable=False)
    instruments: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    mood: Mapped[str] = mapped_column(String(128), nullable=False)
    sound_effects: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    extraction: Mapped[Optional["ExtractionResult"]] = relationship(back_populates="audio")


class ExtractionResult(TimestampMixin, Base):
    """Full structured content extraction produced from a user prompt."""

    __tablename__ = "extraction_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Core content fields
    topic: Mapped[str] = mapped_column(String(256), nullable=False)
    theme: Mapped[str] = mapped_column(String(256), nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    emotional_tone: Mapped[str] = mapped_column(String(128), nullable=False)
    setting: Mapped[str] = mapped_column(String(256), nullable=False)

    # Flat keyword arrays
    action_keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    content_warnings: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    # Nested structures stored as JSONB
    # characters: list[{name, description, role, traits}]
    characters: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    # plot: {summary, points, conflict, resolution} or null
    plot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    video_id: Mapped[int] = mapped_column(Integer, ForeignKey("video_contexts.id"), nullable=False)
    audio_id: Mapped[int] = mapped_column(Integer, ForeignKey("audio_contexts.id"), nullable=False)

    video: Mapped[VideoContext] = relationship(back_populates="extraction")
    audio: Mapped[AudioContext] = relationship(back_populates="extraction")
