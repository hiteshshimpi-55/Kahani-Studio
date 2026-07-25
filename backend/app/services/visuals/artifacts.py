"""Publish media to S3 and register rows in Postgres ``visual_media_assets``.

Local DATA_DIR files are a working cache (kept by default). Canonical blobs
live in S3; APIs resolve presigned URLs via the registry.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.integrations import s3 as s3_client
from app.repository import visual_assets as registry

log = logging.getLogger(__name__)

KIND_LOOKBOOK = "lookbook"
KIND_SHOT = "shot"
KIND_VIDEO = "video"
KIND_PLAN = "plan"
KIND_CHARACTERS = "characters"
KIND_AUDIO = "audio_result"
KIND_TTS = "tts"

MEDIA_SUFFIXES = {".mp3", ".mp4", ".png", ".jpg", ".jpeg", ".webp", ".json", ".wav"}


def s3_key_for(series_id: str, kind: str, asset_key: str) -> str:
    """Stable object key. TTS uses tts/; visuals use visuals/{series}/{kind}/."""
    safe_key = asset_key.lstrip("/")
    if kind == KIND_TTS:
        return f"tts/{series_id}/{safe_key}"
    return f"visuals/{series_id}/{kind}/{safe_key}"


def publish(
    local_path: Path,
    *,
    series_id: str,
    kind: str,
    asset_key: str | None = None,
    delete_local: bool = False,
) -> str:
    """Upload file → upsert DB row. Local file kept unless delete_local=True."""
    if not local_path.exists():
        raise FileNotFoundError(str(local_path))
    key_name = asset_key or local_path.name
    ct = s3_client.content_type_for(local_path)
    if not s3_client.s3_enabled():
        local_key = str(local_path.resolve())
        log.warning(
            "s3_disabled registering_local series=%s kind=%s file=%s",
            series_id, kind, key_name,
        )
        registry.upsert_asset(
            series_id=series_id,
            kind=kind,
            asset_key=key_name,
            s3_key=local_key,
            content_type=ct,
        )
        return local_key

    s3_key = s3_key_for(series_id, kind, key_name)
    s3_client.upload_file(local_path, s3_key, content_type=ct)
    registry.upsert_asset(
        series_id=series_id,
        kind=kind,
        asset_key=key_name,
        s3_key=s3_key,
        content_type=ct,
    )
    if delete_local:
        try:
            local_path.unlink(missing_ok=True)
        except OSError:
            pass
    return s3_key


def publish_tree(
    local_dir: Path,
    *,
    series_id: str,
    kind: str,
) -> dict[str, str]:
    """Upload every media file directly under ``local_dir`` (non-recursive)."""
    uploaded: dict[str, str] = {}
    if not local_dir.is_dir():
        return uploaded
    for path in sorted(local_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in MEDIA_SUFFIXES:
            continue
        try:
            uploaded[path.name] = publish(
                path, series_id=series_id, kind=kind, delete_local=False,
            )
        except Exception:  # noqa: BLE001
            log.exception("publish_failed series=%s file=%s", series_id, path.name)
    return uploaded


def _resolve_url(s3_key: str) -> str:
    if s3_key.startswith("/") or s3_key.startswith("file:"):
        return s3_key
    if not s3_client.s3_enabled():
        return s3_key
    return s3_client.presigned_url(s3_key)


def ensure_local(
    dest: Path,
    *,
    series_id: str,
    kind: str,
    asset_key: str | None = None,
) -> Path | None:
    """Return dest if present, else download from S3 registry. None if missing."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    key_name = asset_key or dest.name
    row = registry.get_asset(series_id, kind, key_name)
    if row is None:
        s3_key = s3_key_for(series_id, kind, key_name)
        if not s3_client.s3_enabled() or not s3_client.object_exists(s3_key):
            return None
    else:
        s3_key = row.s3_key
        if s3_key.startswith("/") and Path(s3_key).exists():
            if Path(s3_key).resolve() != dest.resolve():
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(Path(s3_key).read_bytes())
            return dest if dest.exists() else Path(s3_key)
    try:
        return s3_client.download_file(s3_key, dest)
    except Exception:  # noqa: BLE001
        log.exception("ensure_local_failed series=%s kind=%s key=%s", series_id, kind, key_name)
        return None


def url_for(series_id: str, kind: str, asset_key: str) -> str | None:
    row = registry.get_asset(series_id, kind, asset_key)
    if row is None:
        return None
    return _resolve_url(row.s3_key)


def urls_by_kind(series_id: str, kind: str) -> dict[str, str]:
    return {
        a.asset_key: _resolve_url(a.s3_key)
        for a in registry.list_assets(series_id, kind)
    }


def asset_map(series_id: str) -> dict[str, dict[str, str]]:
    """kind → {asset_key → presigned url}."""
    out: dict[str, dict[str, str]] = {}
    for a in registry.list_assets(series_id):
        out.setdefault(a.kind, {})[a.asset_key] = _resolve_url(a.s3_key)
    return out


def hydrate_audio_paths(series_id: str, audio_result: dict) -> dict:
    """Rewrite preview/bed/stem paths to local cache, pulling from S3 if needed."""
    from app.core.config import settings

    out_dir = Path(settings.data_dir) / "tts" / series_id
    out_dir.mkdir(parents=True, exist_ok=True)

    def _fix(field: str) -> None:
        raw = audio_result.get(field)
        if not raw:
            return
        name = Path(str(raw)).name
        dest = out_dir / name
        got = ensure_local(dest, series_id=series_id, kind=KIND_TTS, asset_key=name)
        if got is not None:
            audio_result[field] = str(got)

    _fix("preview_mp3")
    _fix("bed_mp3")

    for stem in audio_result.get("stems") or []:
        raw = stem.get("path")
        if not raw:
            continue
        name = Path(str(raw)).name
        dest = out_dir / name
        got = ensure_local(dest, series_id=series_id, kind=KIND_TTS, asset_key=name)
        if got is not None:
            stem["path"] = str(got)

    for clip in audio_result.get("sfx_clips") or []:
        raw = clip.get("path")
        if not raw:
            continue
        name = Path(str(raw)).name
        dest = out_dir / name
        got = ensure_local(dest, series_id=series_id, kind=KIND_TTS, asset_key=name)
        if got is not None:
            clip["path"] = str(got)

    return audio_result
