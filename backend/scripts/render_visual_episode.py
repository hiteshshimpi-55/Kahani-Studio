#!/usr/bin/env python3
"""End-to-end: ScriptPackage → audio render → visual episode (9:16 MP4).

Usage:
    # Full run (audio + visuals) on the crime fixture:
    python -m scripts.render_visual_episode app/fixtures/script_crime_mystery.json \
        --series-id crime_v1 --max-sec 60

    # Reuse a previous audio render (audio_result.json saved by this script):
    python -m scripts.render_visual_episode app/fixtures/script_crime_mystery.json \
        --series-id crime_v1 --reuse-audio

    # Director plan only (no image spend):
    python -m scripts.render_visual_episode ... --plan-only
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from app.core.config import settings
from app.services.audiobook.service import AudiobookService
from app.services.visuals import VisualEpisodeService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s — %(message)s",
)
log = logging.getLogger("render_visual")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render visual episode from ScriptPackage")
    parser.add_argument("script", type=Path, help="Path to ScriptPackage JSON")
    parser.add_argument("--series-id", default="visual_preview")
    parser.add_argument("--max-sec", type=float, default=60.0)
    parser.add_argument("--plan-only", action="store_true", help="Stop after the director plan (no images)")
    parser.add_argument("--no-llm", action="store_true", help="Use heuristic director (no Gemini text)")
    parser.add_argument("--reuse-audio", action="store_true", help="Reuse saved audio_result.json for this series")
    parser.add_argument("--no-sfx", action="store_true")
    parser.add_argument("--no-bed", action="store_true")
    args = parser.parse_args(argv)

    if not args.script.exists():
        log.error("script not found: %s", args.script)
        return 2
    package = json.loads(args.script.read_text())
    log.info("script: %s", package.get("title"))

    if not args.plan_only and not (settings.gemini_api_key or "").strip():
        log.error("GEMINI_API_KEY is not set — needed for lookbook + stills (use --plan-only with --no-llm to dry run)")
        return 2

    visuals = VisualEpisodeService()
    out_dir = visuals.out_dir(args.series_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_json = out_dir / "audio_result.json"

    if args.reuse_audio and audio_json.exists():
        audio_result = json.loads(audio_json.read_text())
        log.info("reusing audio render: %.1fs, %d timeline events",
                 audio_result.get("duration_sec", 0), len(audio_result.get("timeline") or []))
    else:
        if not (settings.elevenlabs_api_key or "").strip():
            log.error("ELEVENLABS_API_KEY is not set — cannot render audio")
            return 2
        audio_result = AudiobookService().render_preview(
            package,
            series_id=f"visual_{args.series_id}",
            max_sec=args.max_sec,
            concat=True,
            with_sfx=not args.no_sfx,
            with_bed=not args.no_bed,
        )
        audio_json.write_text(json.dumps(audio_result, indent=2, ensure_ascii=False))
        log.info("audio rendered: %.1fs → %s", audio_result.get("duration_sec", 0),
                 audio_result.get("preview_mp3"))

    result = visuals.render_episode(
        package,
        audio_result,
        series_id=args.series_id,
        use_llm_director=not args.no_llm,
        plan_only=args.plan_only,
    )

    print(json.dumps({k: v for k, v in result.items() if k != "plan"},
                     indent=2, ensure_ascii=False))
    if result.get("video_path"):
        print(f"\n  WATCH: {result['video_path']}")
    elif result.get("plan_path"):
        print(f"\n  PLAN: {result['plan_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
