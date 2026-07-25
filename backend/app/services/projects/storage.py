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


def run_screenplay_path(project_id: str, run_id: str) -> Path:
    return runs_dir(project_id, run_id) / "screenplay.md"


def run_package_path(project_id: str, run_id: str) -> Path:
    return runs_dir(project_id, run_id) / "script.json"


def read_run_screenplay(project_id: str, run_id: str) -> str:
    """Read screenplay for a run (new fixed path, then legacy versioned files)."""
    primary = run_screenplay_path(project_id, run_id)
    if primary.exists():
        return primary.read_text(encoding="utf-8")
    out = runs_dir(project_id, run_id)
    legacy = sorted(out.glob("screenplay.v*.md"))
    if legacy:
        return legacy[-1].read_text(encoding="utf-8")
    return ""


def read_run_package(project_id: str, run_id: str) -> dict:
    primary = run_package_path(project_id, run_id)
    if primary.exists():
        import json

        try:
            data = json.loads(primary.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    out = runs_dir(project_id, run_id)
    legacy = sorted(out.glob("script.v*.json"))
    if legacy:
        import json

        try:
            data = json.loads(legacy[-1].read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


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
