"""Project artifact helpers — object keys with S3 / DATA_DIR via ArtifactStorage."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path

from app.core.config import settings
from app.integrations.s3 import get_artifact_storage

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".md", ".txt", ".markdown"}


def project_root(project_id: str) -> Path:
    return Path(settings.data_dir) / "projects" / project_id


def attachments_dir(project_id: str) -> Path:
    path = project_root(project_id) / "attachments"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runs_dir(project_id: str, run_id: str) -> Path:
    """Local working dir (DATA_DIR). Prefer object-key helpers for shared artifacts."""
    path = project_root(project_id) / "runs" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_object_prefix(project_id: str, run_id: str) -> str:
    return f"projects/{project_id}/runs/{run_id}"


def run_screenplay_key(project_id: str, run_id: str) -> str:
    return f"{run_object_prefix(project_id, run_id)}/screenplay.md"


def run_package_key(project_id: str, run_id: str) -> str:
    return f"{run_object_prefix(project_id, run_id)}/script.json"


def run_source_key(project_id: str, run_id: str) -> str:
    return f"{run_object_prefix(project_id, run_id)}/source.md"


def run_versioned_screenplay_key(project_id: str, run_id: str, version: int) -> str:
    return f"{run_object_prefix(project_id, run_id)}/screenplay.v{version}.md"


def run_versioned_package_key(project_id: str, run_id: str, version: int) -> str:
    return f"{run_object_prefix(project_id, run_id)}/script.v{version}.json"


# Back-compat aliases used by older call sites / local path helpers
def run_screenplay_path(project_id: str, run_id: str) -> Path:
    return runs_dir(project_id, run_id) / "screenplay.md"


def run_package_path(project_id: str, run_id: str) -> Path:
    return runs_dir(project_id, run_id) / "script.json"


def write_run_screenplay(project_id: str, run_id: str, screenplay: str) -> str:
    key = run_screenplay_key(project_id, run_id)
    get_artifact_storage().put_text(key, screenplay, content_type="text/markdown; charset=utf-8")
    return key


def write_run_package(project_id: str, run_id: str, package: dict) -> str:
    key = run_package_key(project_id, run_id)
    get_artifact_storage().put_text(
        key,
        json.dumps(package, ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    return key


def write_run_source(project_id: str, run_id: str, source_md: str) -> str:
    key = run_source_key(project_id, run_id)
    get_artifact_storage().put_text(key, source_md, content_type="text/markdown; charset=utf-8")
    return key


def write_versioned_screenplay(
    project_id: str, run_id: str, version: int, screenplay: str
) -> str:
    key = run_versioned_screenplay_key(project_id, run_id, version)
    get_artifact_storage().put_text(key, screenplay, content_type="text/markdown; charset=utf-8")
    return key


def write_versioned_package(project_id: str, run_id: str, version: int, package: dict) -> str:
    key = run_versioned_package_key(project_id, run_id, version)
    get_artifact_storage().put_text(
        key,
        json.dumps(package, ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    return key


def _read_text_key(key: str) -> str:
    try:
        return get_artifact_storage().get_text(key)
    except FileNotFoundError:
        return ""


def read_run_screenplay(project_id: str, run_id: str) -> str:
    """Read screenplay for a run (object store, then local legacy paths)."""
    text = _read_text_key(run_screenplay_key(project_id, run_id))
    if text:
        return text

    # Local absolute-path layout from before object-key storage
    primary = run_screenplay_path(project_id, run_id)
    if primary.exists():
        return primary.read_text(encoding="utf-8")
    out = runs_dir(project_id, run_id)
    legacy = sorted(out.glob("screenplay.v*.md"))
    if legacy:
        return legacy[-1].read_text(encoding="utf-8")
    return ""


def read_run_package(project_id: str, run_id: str) -> dict:
    key = run_package_key(project_id, run_id)
    raw = _read_text_key(key)
    if raw:
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            logger.warning("invalid_run_package key=%s", key)

    primary = run_package_path(project_id, run_id)
    if primary.exists():
        try:
            data = json.loads(primary.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    out = runs_dir(project_id, run_id)
    legacy = sorted(out.glob("script.v*.json"))
    if legacy:
        try:
            data = json.loads(legacy[-1].read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def read_screenplay_artifact(storage_path: str) -> str:
    """Read a script screenplay by stored object key or legacy absolute path."""
    if not storage_path:
        return ""
    try:
        return get_artifact_storage().get_text(storage_path)
    except FileNotFoundError:
        return ""


def attachment_object_key(project_id: str, attachment_id: str, filename: str) -> str:
    """Object key for artifact storage (S3 or DATA_DIR layout)."""
    return f"projects/{project_id}/attachments/{attachment_id}_{safe_filename(filename)}"


def attachment_storage_path(project_id: str, attachment_id: str, filename: str) -> Path:
    """Legacy local path helper (prefer attachment_object_key + ArtifactStorage)."""
    return attachments_dir(project_id) / f"{attachment_id}_{safe_filename(filename)}"


def local_chunks_dir(project_id: str) -> Path:
    path = project_root(project_id) / "chunks"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^\w.\-]+", "_", base).strip("._")
    return cleaned or "upload.txt"


def checksum_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_allowed_filename(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS
