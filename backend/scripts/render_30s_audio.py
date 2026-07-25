#!/usr/bin/env python3
"""Cast + synthesize a ScriptPackage preview via ElevenLabs.

Usage:
    # Default fixture (Dandi March):
    python -m scripts.render_30s_audio

    # Custom script JSON:
    python -m scripts.render_30s_audio path/to/script.json

    # Override series_id or duration:
    python -m scripts.render_30s_audio --series-id dandi_v2 --max-sec 45
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from app.core.config import settings
from app.services.audiobook.service import AudiobookService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
)
log = logging.getLogger("render_audio")

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "app" / "fixtures"


def load_package(path: Path | None) -> dict:
    if path and path.exists():
        log.info("loading script from %s", path)
        return json.loads(path.read_text())

    for name in ("script_dandi_march.json", "script_30s_horror.json"):
        fixture = FIXTURES_DIR / name
        if fixture.exists():
            log.info("using fixture %s", fixture)
            return json.loads(fixture.read_text())

    log.error("No script file or fixture found")
    sys.exit(2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render audiobook preview from ScriptPackage")
    parser.add_argument("script", nargs="?", type=Path, help="Path to ScriptPackage JSON")
    parser.add_argument("--series-id", default="preview", help="Output subfolder name (default: preview)")
    parser.add_argument("--max-sec", type=float, default=30.0, help="Max preview seconds (default: 30)")
    parser.add_argument("--no-sfx", action="store_true", help="Skip SFX generation")
    args = parser.parse_args(argv)

    if not (settings.elevenlabs_api_key or "").strip():
        log.error("ELEVENLABS_API_KEY is not set")
        return 2

    log.info("data_dir=%s  model=%s", settings.data_dir, settings.elevenlabs_default_model_id)

    package = load_package(args.script)
    title = package.get("title", "untitled")
    log.info("script: %s  language=%s", title, package.get("language"))

    result = AudiobookService().render_preview(
        package,
        series_id=args.series_id,
        max_sec=args.max_sec,
        concat=True,
        with_sfx=not args.no_sfx,
    )

    summary = {
        "title": result["title"],
        "language": result["language"],
        "model_id": result["model_id"],
        "line_count": result["line_count"],
        "sfx_cue_count": result["sfx_cue_count"],
        "sfx_clip_count": result.get("sfx_clip_count", 0),
        "voice_map": result["voice_map"],
        "stems": [
            {
                "seq_id": s["seq_id"],
                "speaker": s["speaker"],
                "voice_id": s["voice_id"],
                "spoken_text": s["spoken_text"],
                "bytes": s["bytes"],
            }
            for s in result["stems"]
        ],
        "sfx_clips": [
            {"sfx_id": c["sfx_id"], "cue": c["cue"], "bytes": c["bytes"]}
            for c in result.get("sfx_clips") or []
        ],
        "preview_mp3": result["preview_mp3"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if result.get("preview_mp3"):
        print(f"\n  LISTEN: {result['preview_mp3']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
