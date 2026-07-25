"""Map visual episode artifacts (lookbook / shots / video) to S3.

Revision ID: 002_visual_media_assets
Revises: 001_visual_identity
Create Date: 2026-07-26
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_visual_media_assets"
down_revision: Union[str, None] = "001_visual_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "visual_media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("series_id", sa.String(128), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("asset_key", sa.String(256), nullable=False),
        sa.Column("s3_key", sa.String(1024), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "series_id",
            "kind",
            "asset_key",
            name="uq_visual_media_assets_series_kind_key",
        ),
    )
    op.create_index(
        "ix_visual_media_assets_series_id",
        "visual_media_assets",
        ["series_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_visual_media_assets_series_id", table_name="visual_media_assets")
    op.drop_table("visual_media_assets")
