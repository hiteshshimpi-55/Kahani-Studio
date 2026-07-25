"""Postgres registry: series_id + kind + asset_key → S3 object key.

Uses a sync engine so ARQ worker threads can upsert without an event loop.
"""

from __future__ import annotations

import logging
import uuid
from functools import lru_cache

from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.repository.models.visual_media import VisualMediaAsset

log = logging.getLogger(__name__)

__all__ = ["VisualMediaAsset", "upsert_asset", "get_asset", "list_assets"]


def _sync_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql+asyncpg://")
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    # psycopg (v3) wants sslmode=, not asyncpg's ssl=
    url = url.replace("ssl=require", "sslmode=require")
    url = url.replace("ssl=true", "sslmode=require")
    return url


@lru_cache(maxsize=1)
def _session_factory():
    engine = create_engine(
        _sync_url(settings.database_url),
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=5,
    )
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def upsert_asset(
    *,
    series_id: str,
    kind: str,
    asset_key: str,
    s3_key: str,
    content_type: str = "",
) -> VisualMediaAsset:
    Session = _session_factory()
    with Session() as session:
        stmt = (
            insert(VisualMediaAsset)
            .values(
                id=uuid.uuid4(),
                series_id=series_id,
                kind=kind,
                asset_key=asset_key,
                s3_key=s3_key,
                content_type=content_type or "",
            )
            .on_conflict_do_update(
                constraint="uq_visual_media_assets_series_kind_key",
                set_={
                    "s3_key": s3_key,
                    "content_type": content_type or "",
                },
            )
            .returning(VisualMediaAsset)
        )
        row = session.execute(stmt).scalar_one()
        session.commit()
        log.info(
            "visual_asset_upsert series=%s kind=%s key=%s",
            series_id, kind, asset_key,
        )
        return row


def get_asset(series_id: str, kind: str, asset_key: str) -> VisualMediaAsset | None:
    Session = _session_factory()
    with Session() as session:
        return session.scalar(
            select(VisualMediaAsset).where(
                VisualMediaAsset.series_id == series_id,
                VisualMediaAsset.kind == kind,
                VisualMediaAsset.asset_key == asset_key,
            )
        )


def list_assets(series_id: str, kind: str | None = None) -> list[VisualMediaAsset]:
    Session = _session_factory()
    with Session() as session:
        stmt = select(VisualMediaAsset).where(VisualMediaAsset.series_id == series_id)
        if kind:
            stmt = stmt.where(VisualMediaAsset.kind == kind)
        stmt = stmt.order_by(VisualMediaAsset.kind, VisualMediaAsset.asset_key)
        return list(session.scalars(stmt).all())
