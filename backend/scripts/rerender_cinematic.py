#!/usr/bin/env python3
"""Re-plan + re-render cinematic scenes for an existing series (identity sheets reused)."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import time
from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.core.db.session import AsyncSessionLocal
from app.services.visual.renderer import VisualRenderService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("rerender_cinematic")

SERIES = UUID("a9d53fef-5f17-4975-b875-b02e41b074aa")


def pause(sec: float, why: str) -> None:
    log.info("pause %.0fs (%s)", sec, why)
    time.sleep(sec)


async def main() -> None:
    t0 = time.time()
    fixture = json.loads(
        (Path(__file__).resolve().parents[1] / "app/fixtures/visual_horror_30s.json").read_text()
    )
    parts_dir = Path(settings.data_dir) / "visual" / str(SERIES) / "parts" / "p1"
    if parts_dir.exists():
        shutil.rmtree(parts_dir)
        log.info("cleared old stills %s", parts_dir)

    async with AsyncSessionLocal() as session:
        try:
            vis = VisualRenderService(session)
            log.info("re-plan cinematic track")
            track = await vis.plan(
                series_id=SERIES,
                part=1,
                beats=fixture["beats"],
                seq_timings=fixture["seq_timings"],
                part_duration_sec=fixture["part_duration_sec"],
                persist=True,
            )
            for s in track.shots:
                log.info(
                    "plan %s trigger=%s size=%s framing=%s faces=%s intent=%s",
                    s.shot_id,
                    s.trigger_reason,
                    s.shot_size.value,
                    s.framing.value,
                    len(s.characters),
                    (s.visual_intent or "")[:120],
                )
                log.info("  prompt=%s", (s.compiled_prompt or "")[:220])

            log.info("render %s stills with Flux scene mode", len(track.shots))
            for i in range(1, len(track.shots) + 1):
                pause(12, f"before still {i}/{len(track.shots)}")
                rendered = await vis.render_track(series_id=SERIES, part=1, max_shots=i)
                shot = rendered.shots[i - 1]
                p = Path(shot.asset_url) if shot.asset_url else None
                log.info(
                    "still %s bytes=%s model_face_lock=%s",
                    shot.shot_id,
                    p.stat().st_size if p and p.exists() else 0,
                    bool(shot.characters) and shot.shot_size.value in {"cu", "ecu"},
                )

            preview = Path(settings.data_dir) / "visual" / str(SERIES) / "preview_v2"
            preview.mkdir(parents=True, exist_ok=True)
            import subprocess

            for webp in sorted(parts_dir.glob("*.webp")):
                jpg = preview / f"{webp.stem}.jpg"
                subprocess.run(
                    ["sips", "-s", "format", "jpeg", str(webp), "--out", str(jpg)],
                    check=False,
                    capture_output=True,
                )
                log.info("preview %s", jpg)

            await session.commit()
            log.info("DONE seconds=%.1f out=%s", time.time() - t0, parts_dir)
        except Exception:
            await session.rollback()
            log.exception("rerender_failed")
            raise


if __name__ == "__main__":
    asyncio.run(main())
