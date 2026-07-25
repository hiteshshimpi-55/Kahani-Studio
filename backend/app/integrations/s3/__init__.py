"""Thin S3 helpers for visual (and other) artifacts.

Uses ARTIFACTS_BUCKET from Terraform/ECS. Credentials are optional —
ECS task role is preferred; local/dev may set AWS_ACCESS_KEY_ID.
"""

from __future__ import annotations

import logging
import mimetypes
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.integrations.s3.storage import ArtifactStorage, get_artifact_storage

log = logging.getLogger(__name__)

__all__ = [
    "ArtifactStorage",
    "S3NotConfiguredError",
    "get_artifact_storage",
    "s3_enabled",
    "require_bucket",
    "content_type_for",
    "upload_file",
    "download_file",
    "object_exists",
    "presigned_url",
    "s3_uri",
]


class S3NotConfiguredError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _client():
    import boto3
    from botocore.config import Config

    # ap-south-2 (and other newer regions) reject global s3.amazonaws.com
    # hosts — always use the regional endpoint for sign + fetch.
    region = (settings.aws_region or "ap-south-2").strip()
    kwargs: dict = {
        "region_name": region,
        "endpoint_url": f"https://s3.{region}.amazonaws.com",
        "config": Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    }
    key = (settings.aws_access_key_id or "").strip()
    secret = (settings.aws_secret_access_key or "").strip()
    if key and secret:
        kwargs["aws_access_key_id"] = key
        kwargs["aws_secret_access_key"] = secret
    return boto3.client("s3", **kwargs)


def s3_enabled() -> bool:
    return bool((settings.artifacts_bucket or "").strip())


def require_bucket() -> str:
    bucket = (settings.artifacts_bucket or "").strip()
    if not bucket:
        raise S3NotConfiguredError(
            "ARTIFACTS_BUCKET is not set — configure the Terraform artifacts bucket"
        )
    return bucket


def content_type_for(path: Path | str) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def upload_file(local_path: Path, s3_key: str, *, content_type: str | None = None) -> str:
    """Upload a local file. Returns the object key."""
    bucket = require_bucket()
    ct = content_type or content_type_for(local_path)
    _client().upload_file(
        str(local_path),
        bucket,
        s3_key,
        ExtraArgs={"ContentType": ct},
    )
    log.info("s3_upload bucket=%s key=%s", bucket, s3_key)
    return s3_key


def download_file(s3_key: str, dest: Path) -> Path:
    bucket = require_bucket()
    dest.parent.mkdir(parents=True, exist_ok=True)
    _client().download_file(bucket, s3_key, str(dest))
    log.info("s3_download bucket=%s key=%s -> %s", bucket, s3_key, dest.name)
    return dest


def object_exists(s3_key: str) -> bool:
    if not s3_enabled():
        return False
    bucket = require_bucket()
    try:
        _client().head_object(Bucket=bucket, Key=s3_key)
        return True
    except Exception:  # noqa: BLE001
        return False


def presigned_url(s3_key: str, *, expires_in: int | None = None) -> str:
    bucket = require_bucket()
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=expires_in or settings.s3_presign_expires_sec,
    )


def s3_uri(s3_key: str) -> str:
    return f"s3://{require_bucket()}/{s3_key}"
