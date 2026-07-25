"""Project filesystem helpers under DATA_DIR."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.core.config import settings

ALLOWED_EXTENSIONS = {".md", ".txt", ".markdown"}


def project_root(project_id: str) -> Path:
    return Path(settings.data_dir) / "projects" / project_id


def attachments_dir(project_id: str) -> Path:
    path = project_root(project_id) / "attachments"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runs_dir(project_id: str, run_id: str) -> Path:
    path = project_root(project_id) / "runs" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def local_chunks_dir(project_id: str) -> Path:
    path = project_root(project_id) / "chunks"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^\w.\-]+", "_", base).strip("._")
    return cleaned or "upload.txt"


def attachment_storage_path(project_id: str, attachment_id: str, filename: str) -> Path:
    return attachments_dir(project_id) / f"{attachment_id}_{safe_filename(filename)}"


def checksum_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_allowed_filename(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS
