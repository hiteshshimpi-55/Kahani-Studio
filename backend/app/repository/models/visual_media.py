"""Maps logical media artifacts (lookbook / shots / video / tts) to S3 keys."""

from __future__ import annotations

import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.repository.models.base.base import Base
from app.repository.models.base.mixins import TimestampMixin


class VisualMediaAsset(TimestampMixin, Base):
    __tablename__ = "visual_media_assets"
    __table_args__ = (
        UniqueConstraint(
            "series_id", "kind", "asset_key", name="uq_visual_media_assets_series_kind_key"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    series_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_key: Mapped[str] = mapped_column(String(256), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False, default="")
