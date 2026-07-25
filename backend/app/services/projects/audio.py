"""Script draft → ElevenLabs audiobook render (status sidecar, no DB migration)."""

from __future__ import annotations

import json
import logging
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.audiobook.service import AudiobookService

log = logging.getLogger(__name__)

AUDIO_STATUS_FILE = "audio_status.json"
AUDIO_FILE = "episode.mp3"


def audio_status_path(storage_dir: str | Path) -> Path:
    return Path(storage_dir) / AUDIO_STATUS_FILE


def audio_file_path(storage_dir: str | Path) -> Path:
    return Path(storage_dir) / AUDIO_FILE


def read_audio_status(storage_dir: str | Path) -> dict[str, Any] | None:
    path = audio_status_path(storage_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def write_audio_status(storage_dir: str | Path, payload: dict[str, Any]) -> dict[str, Any]:
    out_dir = Path(storage_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    body = {
        **payload,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    audio_status_path(out_dir).write_text(
        json.dumps(body, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return body


def package_with_screenplay(package: dict[str, Any], screenplay_md: str) -> dict[str, Any]:
    """Ensure parts[0].screenplay matches the draft markdown used for TTS."""
    pkg = deepcopy(package) if isinstance(package, dict) else {}
    parts = list(pkg.get("parts") or [])
    text = (screenplay_md or "").strip()
    if not parts:
        parts = [
            {
                "part_number": 1,
                "title": pkg.get("title") or "Episode 1",
                "target_duration_sec": 300,
                "screenplay": text,
                "cliff_out": "",
                "sfx_cues": [],
            }
        ]
    else:
        first = dict(parts[0] or {})
        if text:
            first["screenplay"] = text
        parts[0] = first
    pkg["parts"] = parts
    if not pkg.get("language"):
        pkg["language"] = "hi"
    return pkg


def render_script_audio(
    *,
    project_id: str,
    script_id: str,
    storage_dir: str,
    package: dict[str, Any],
    screenplay_md: str,
    max_sec: float = 300.0,
    voice_provider: str | None = None,
    with_sfx: bool = True,
    with_bed: bool = True,
) -> dict[str, Any]:
    """Render audiobook preview into the script storage dir. Sync / worker entry."""
    provider = (voice_provider or settings.tts_provider or "elevenlabs").strip().lower()
    write_audio_status(
        storage_dir,
        {
            "status": "running",
            "error": None,
            "audio_url": None,
            "voice_provider": provider,
            "project_id": project_id,
            "script_id": script_id,
        },
    )

    try:
        pkg = package_with_screenplay(package, screenplay_md)
        result = AudiobookService().render_preview(
            pkg,
            series_id=f"script-{script_id}",
            max_sec=max_sec,
            with_sfx=with_sfx,
            with_bed=with_bed,
            voice_provider=provider,
        )
        preview = result.get("preview_mp3")
        if not preview or not Path(preview).is_file():
            raise RuntimeError("Audiobook render produced no MP3")

        dest = audio_file_path(storage_dir)
        shutil.copy2(preview, dest)
        audio_url = f"/api/v1/projects/{project_id}/scripts/{script_id}/audio/file"
        status = write_audio_status(
            storage_dir,
            {
                "status": "succeeded",
                "error": None,
                "audio_path": str(dest),
                "audio_url": audio_url,
                "voice_provider": result.get("voice_provider") or provider,
                "line_count": result.get("line_count"),
                "sfx_clip_count": result.get("sfx_clip_count"),
                "title": result.get("title"),
                "project_id": project_id,
                "script_id": script_id,
            },
        )
        log.info(
            "script_audio_ok project=%s script=%s lines=%s",
            project_id,
            script_id,
            result.get("line_count"),
        )
        return status
    except Exception as exc:
        log.exception("script_audio_failed project=%s script=%s", project_id, script_id)
        return write_audio_status(
            storage_dir,
            {
                "status": "failed",
                "error": str(exc),
                "audio_url": None,
                "voice_provider": provider,
                "project_id": project_id,
                "script_id": script_id,
            },
        )
