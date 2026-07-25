#!/usr/bin/env python3
"""Upload existing local DATA_DIR media to S3 and register Postgres rows.

Does NOT delete local files.

Usage (from backend/, with .env loaded):
    PYTHONPATH=. python -m scripts.upload_local_media_to_s3
    PYTHONPATH=. python -m scripts.upload_local_media_to_s3 --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.core.config import settings
from app.integrations import s3 as s3_client
from app.services.visuals import artifacts as media

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
)
log = logging.getLogger("upload_local_media")


def _upload_tts(data_dir: Path, *, dry_run: bool) -> int:
    root = data_dir / "tts"
    if not root.is_dir():
        log.warning("no tts dir at %s", root)
        return 0
    count = 0
    for series_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        series_id = series_dir.name
        files = [
            p for p in series_dir.iterdir()
            if p.is_file() and p.suffix.lower() in media.MEDIA_SUFFIXES
        ]
        log.info("tts series=%s files=%d", series_id, len(files))
        if dry_run:
            count += len(files)
            continue
        uploaded = media.publish_tree(series_dir, series_id=series_id, kind=media.KIND_TTS)
        count += len(uploaded)
    return count


def _upload_visuals(data_dir: Path, *, dry_run: bool) -> int:
    root = data_dir / "visuals"
    if not root.is_dir():
        log.warning("no visuals dir at %s (already cleared?)", root)
        return 0
    count = 0
    kind_map = {
        "lookbook": media.KIND_LOOKBOOK,
        "shots": media.KIND_SHOT,
        "clips": media.KIND_VIDEO,
    }
    for series_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        series_id = series_dir.name
        for sub, kind in kind_map.items():
            folder = series_dir / sub
            if not folder.is_dir():
                continue
            files = [p for p in folder.iterdir() if p.is_file()]
            log.info("visuals series=%s kind=%s files=%d", series_id, kind, len(files))
            if dry_run:
                count += len(files)
                continue
            for path in files:
                media.publish(path, series_id=series_id, kind=kind, delete_local=False)
                count += 1
        for name, kind in (
            ("episode.mp4", media.KIND_VIDEO),
            ("episode_silent.mp4", media.KIND_VIDEO),
            ("plan.json", media.KIND_PLAN),
            ("characters.json", media.KIND_CHARACTERS),
            ("audio_result.json", media.KIND_AUDIO),
        ):
            path = series_dir / name
            if not path.is_file():
                continue
            log.info("visuals series=%s file=%s", series_id, name)
            if dry_run:
                count += 1
                continue
            media.publish(
                path, series_id=series_id, kind=kind, asset_key=name, delete_local=False,
            )
            count += 1
    return count


def _upload_voice_tests(data_dir: Path, *, dry_run: bool) -> int:
    root = data_dir / "voice_tests"
    if not root.is_dir():
        return 0
    count = 0
    for series_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        series_id = f"voice_tests__{series_dir.name}"
        files = [
            p for p in series_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in media.MEDIA_SUFFIXES
        ]
        log.info("voice_tests series=%s files=%d", series_id, len(files))
        if dry_run:
            count += len(files)
            continue
        for path in files:
            rel = path.relative_to(series_dir).as_posix().replace("/", "__")
            media.publish(
                path,
                series_id=series_id,
                kind=media.KIND_TTS,
                asset_key=rel,
                delete_local=False,
            )
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Override DATA_DIR (default: settings.data_dir)",
    )
    args = parser.parse_args(argv)

    data_dir = args.data_dir or Path(settings.data_dir)
    log.info("data_dir=%s bucket=%s region=%s", data_dir, settings.artifacts_bucket, settings.aws_region)

    if not args.dry_run and not s3_client.s3_enabled():
        log.error("ARTIFACTS_BUCKET is not set")
        return 2

    if not args.dry_run:
        try:
            import boto3  # noqa: F401
        except ImportError:
            log.error("boto3 not installed — pip install boto3")
            return 2

    total = 0
    total += _upload_tts(data_dir, dry_run=args.dry_run)
    total += _upload_visuals(data_dir, dry_run=args.dry_run)
    total += _upload_voice_tests(data_dir, dry_run=args.dry_run)
    log.info("%s files=%d", "would_upload" if args.dry_run else "uploaded", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
