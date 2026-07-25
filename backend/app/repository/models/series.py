"""Series bible — characters, identity sheets, locations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.repository.models.base.base import Base
from app.repository.models.base.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.repository.models.visual import VisualTrackRecord

CHARACTER_ASSET_KINDS = (
    "turnaround_front",
    "turnaround_three_quarter",
    "turnaround_side",
    "full_body",
    "expr_neutral",
    "expr_fear",
    "expr_anger",
    "expr_whisper",
    "expr_gasp",
    "expr_dismissive",
    "expr_menace",
)


class Series(TimestampMixin, Base):
    __tablename__ = "series"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    language: Mapped[str] = mapped_column(String(8), default="hi", nullable=False)
    style_bible: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    characters: Mapped[list[Character]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    locations: Mapped[list[Location]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    visual_tracks: Mapped[list[VisualTrackRecord]] = relationship(
        "VisualTrackRecord", back_populates="series", cascade="all, delete-orphan"
    )


class Character(TimestampMixin, Base):
    __tablename__ = "characters"
    __table_args__ = (
        UniqueConstraint("series_id", "name", name="uq_characters_series_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="character", nullable=False)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    age_band: Mapped[str | None] = mapped_column(String(32), nullable=True)
    identity_tokens: Mapped[str] = mapped_column(Text, nullable=False, default="")
    voice_provider_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    series: Mapped[Series] = relationship(back_populates="characters")
    assets: Mapped[list[CharacterAsset]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )


class CharacterAsset(TimestampMixin, Base):
    __tablename__ = "character_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(256), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    character: Mapped[Character] = relationship(back_populates="assets")


class Location(TimestampMixin, Base):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("series_id", "name", name="uq_locations_series_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("series.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    series: Mapped[Series] = relationship(back_populates="locations")
    assets: Mapped[list[LocationAsset]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class LocationAsset(TimestampMixin, Base):
    __tablename__ = "location_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(256), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped[Location] = relationship(back_populates="assets")
