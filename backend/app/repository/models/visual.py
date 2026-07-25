"""Visual track persistence — planned shots + rendered still assets."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.repository.models.base.base import Base
from app.repository.models.base.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.repository.models.series import Series


class VisualTrackRecord(TimestampMixin, Base):
    __tablename__ = "visual_tracks"
    __table_args__ = (
        UniqueConstraint("series_id", "part", name="uq_visual_tracks_series_part"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series.id", ondelete="CASCADE"), nullable=False
    )
    part: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    track_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    series: Mapped[Series] = relationship("Series", back_populates="visual_tracks")
    shot_assets: Mapped[list[VisualShotAsset]] = relationship(
        back_populates="track", cascade="all, delete-orphan"
    )


class VisualShotAsset(TimestampMixin, Base):
    __tablename__ = "visual_shot_assets"
    __table_args__ = (
        UniqueConstraint("track_id", "shot_id", name="uq_visual_shot_assets_track_shot"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("visual_tracks.id", ondelete="CASCADE"),
        nullable=False,
    )
    shot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    track: Mapped[VisualTrackRecord] = relationship(back_populates="shot_assets")
