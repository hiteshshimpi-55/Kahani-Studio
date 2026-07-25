"""S3-backed artifact storage with DATA_DIR filesystem fallback."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class ArtifactStorage:
    """Put/get/delete bytes by object key. Uses S3 when ARTIFACTS_BUCKET is set."""

    def __init__(self, bucket: str | None, region: str, data_dir: str) -> None:
        self.bucket = (bucket or "").strip() or None
        self.region = region
        self.data_dir = Path(data_dir)
        self._client = None
        if self.bucket:
            import boto3

            self._client = boto3.client("s3", region_name=self.region)

    @property
    def uses_s3(self) -> bool:
        return self._client is not None and self.bucket is not None

    def _local_path(self, key: str) -> Path:
        # Keep key layout under DATA_DIR (projects/…, library/…)
        path = self.data_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store bytes; returns the storage key (same as input)."""
        # Legacy absolute filesystem paths (pre object-key rows)
        if key.startswith("/") or (len(key) > 2 and key[1] == ":"):
            path = Path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return key
        if self.uses_s3:
            assert self._client is not None and self.bucket is not None
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return key
        self._local_path(key).write_bytes(data)
        return key

    def put_text(
        self,
        key: str,
        text: str,
        *,
        encoding: str = "utf-8",
        content_type: str = "text/plain; charset=utf-8",
    ) -> str:
        return self.put_bytes(key, text.encode(encoding), content_type=content_type)

    def get_bytes(self, key: str) -> bytes:
        legacy = self._maybe_legacy_path(key)
        if legacy is not None:
            return legacy.read_bytes()
        if self.uses_s3:
            assert self._client is not None and self.bucket is not None
            try:
                resp = self._client.get_object(Bucket=self.bucket, Key=key)
            except Exception as exc:
                if _is_not_found(exc):
                    raise FileNotFoundError(key) from exc
                raise
            return resp["Body"].read()
        path = self._local_path(key)
        if not path.exists():
            raise FileNotFoundError(key)
        return path.read_bytes()

    def get_text(self, key: str, encoding: str = "utf-8", errors: str = "ignore") -> str:
        return self.get_bytes(key).decode(encoding, errors=errors)

    def exists(self, key: str) -> bool:
        legacy = self._maybe_legacy_path(key)
        if legacy is not None:
            return True
        if self.uses_s3:
            assert self._client is not None and self.bucket is not None
            try:
                self._client.head_object(Bucket=self.bucket, Key=key)
                return True
            except Exception as exc:
                if _is_not_found(exc):
                    return False
                raise
        return self._local_path(key).is_file()

    def ensure_local(self, key: str) -> Path:
        """Return a local filesystem path for key, downloading from S3 when needed."""
        legacy = self._maybe_legacy_path(key)
        if legacy is not None:
            return legacy
        local = self._local_path(key)
        if self.uses_s3:
            if not local.is_file():
                local.write_bytes(self.get_bytes(key))
            return local
        if not local.is_file():
            raise FileNotFoundError(key)
        return local

    def delete(self, key: str) -> None:
        legacy = self._maybe_legacy_path(key)
        if legacy is not None:
            try:
                legacy.unlink(missing_ok=True)
            except TypeError:
                if legacy.exists():
                    legacy.unlink()
            return
        if self.uses_s3:
            assert self._client is not None and self.bucket is not None
            try:
                self._client.delete_object(Bucket=self.bucket, Key=key)
            except Exception:
                logger.exception("Failed to delete s3://%s/%s", self.bucket, key)
            return
        path = self._local_path(key)
        if path.exists():
            path.unlink()

    def _maybe_legacy_path(self, storage_path: str) -> Path | None:
        """Support absolute DATA_DIR paths written before object-key storage."""
        if not storage_path:
            return None
        if storage_path.startswith("/") or (len(storage_path) > 2 and storage_path[1] == ":"):
            path = Path(storage_path)
            if path.is_file():
                return path
        return None


def _is_not_found(exc: BaseException) -> bool:
    code = getattr(exc, "response", None)
    if isinstance(code, dict):
        err = code.get("Error") or {}
        if err.get("Code") in {"404", "NoSuchKey", "NotFound", "404 Not Found"}:
            return True
    status = getattr(exc, "response", None)
    if isinstance(status, dict):
        meta = status.get("ResponseMetadata") or {}
        if meta.get("HTTPStatusCode") == 404:
            return True
    name = type(exc).__name__
    return name in {"NoSuchKey", "404", "NotFound"}


@lru_cache(maxsize=1)
def get_artifact_storage() -> ArtifactStorage:
    return ArtifactStorage(
        bucket=settings.artifacts_bucket,
        region=settings.aws_region,
        data_dir=settings.data_dir,
    )
