"""Add staged production fields to project_runs.

Revision ID: 003_run_production_stages
Revises: 002_visual_media_assets
Create Date: 2026-07-26
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_run_production_stages"
down_revision: Union[str, None] = "002_visual_media_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "project_runs",
        sa.Column("current_stage", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "project_runs",
        sa.Column(
            "stage_statuses",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "project_runs",
        sa.Column("audio_s3_key", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "project_runs",
        sa.Column("cover_s3_key", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "project_runs",
        sa.Column("manifest_s3_key", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "project_runs",
        sa.Column("revision_notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("project_runs", "revision_notes")
    op.drop_column("project_runs", "manifest_s3_key")
    op.drop_column("project_runs", "cover_s3_key")
    op.drop_column("project_runs", "audio_s3_key")
    op.drop_column("project_runs", "stage_statuses")
    op.drop_column("project_runs", "current_stage")
