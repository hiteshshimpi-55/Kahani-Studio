#!/usr/bin/env python3
"""Full end-to-end Visual Director smoke (Replicate + Postgres + plan/render)."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

from app.core.config import settings
from app.core.db.session import AsyncSessionLocal, Base, engine
import app.repository.models  # noqa: F401
from app.schemas.identity.request import CharacterSpec, CreateSeriesRequest, LocationSpec
from app.services.identity.service import IdentityService
from app.services.visual.renderer import VisualRenderService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("e2e_visual")


def pause(sec: float, why: str) -> None:
    log.info("pause %.0fs (%s)", sec, why)
    time.sleep(sec)


async def main() -> None:
    t0 = time.time()
    fixture = json.loads(
        (Path(__file__).resolve().parents[1] / "app/fixtures/visual_horror_30s.json").read_text()
    )
    log.info("token=%s data_dir=%s pulid=%s", bool(settings.replicate_api_token), settings.data_dir, settings.replicate_pulid_model)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        try:
            idsvc = IdentityService(session)

            log.info("STEP 1 create_series")
            series = await idsvc.create_series(
                CreateSeriesRequest(
                    title="Ticket to Nowhere — full E2E",
                    language="hi",
                    look="cinematic horror thriller, muted teal-orange, photorealistic film still",
                    max_stills_per_part=5,
                )
            )
            sid = series.id
            log.info("series_id=%s", sid)

            log.info("STEP 2 generate Riya (front + fear)")
            pause(8, "rate limit before first GPU")
            riya = await idsvc.generate_characters(
                sid,
                [
                    CharacterSpec(
                        name="Riya",
                        role="character",
                        gender="female",
                        age_band="20s",
                        identity_tokens=fixture["characters"][0]["identity_tokens"],
                        expressions=["fear"],
                    )
                ],
                generate_images=True,
            )
            for a in riya[0].assets:
                p = Path(a.file_path)
                log.info("  Riya %s bytes=%s", a.kind, p.stat().st_size if p.exists() else 0)
            await idsvc.lock_character(riya[0].id)
            log.info("  Riya locked")

            log.info("STEP 3 generate Arjun (front)")
            pause(12, "rate limit before Arjun")
            arjun = await idsvc.generate_characters(
                sid,
                [
                    CharacterSpec(
                        name="Arjun",
                        role="character",
                        gender="male",
                        age_band="20s",
                        identity_tokens=fixture["characters"][1]["identity_tokens"],
                        expressions=[],
                    )
                ],
                generate_images=True,
            )
            for a in arjun[0].assets:
                p = Path(a.file_path)
                log.info("  Arjun %s bytes=%s", a.kind, p.stat().st_size if p.exists() else 0)

            log.info("STEP 4 generate location")
            pause(12, "rate limit before location")
            locs = await idsvc.generate_locations(
                sid,
                [LocationSpec(**fixture["locations"][0])],
                generate_images=True,
            )
            for a in locs[0].assets:
                p = Path(a.file_path)
                log.info("  Loc %s bytes=%s", a.kind, p.stat().st_size if p.exists() else 0)

            log.info("STEP 5 plan VisualTrack")
            vis = VisualRenderService(session)
            track = await vis.plan(
                series_id=sid,
                part=1,
                beats=fixture["beats"],
                seq_timings=fixture["seq_timings"],
                part_duration_sec=fixture["part_duration_sec"],
                persist=True,
            )
            for s in track.shots:
                log.info(
                    "  plan %s trigger=%s size=%s t=%.1f-%.1f faces=%s",
                    s.shot_id,
                    s.trigger_reason,
                    s.shot_size.value,
                    s.t_start_sec,
                    s.t_end_sec,
                    len(s.characters),
                )

            log.info("STEP 6 render ALL %s stills", len(track.shots))
            # Render one shot at a time so pauses apply between GPU calls
            for i in range(1, len(track.shots) + 1):
                pause(12, f"rate limit before still {i}/{len(track.shots)}")
                rendered = await vis.render_track(series_id=sid, part=1, max_shots=i)
                shot = rendered.shots[i - 1]
                p = Path(shot.asset_url) if shot.asset_url else None
                log.info(
                    "  still %s path=%s bytes=%s",
                    shot.shot_id,
                    shot.asset_url,
                    p.stat().st_size if p and p.exists() else 0,
                )

            log.info("STEP 7 timeline")
            tl = await vis.get_timeline(sid, 1)
            for item in tl["items"]:
                log.info(
                    "  tl %s %.1f-%.1f asset=%s",
                    item["shot_id"],
                    item["t_start_sec"],
                    item["t_end_sec"],
                    bool(item.get("asset_url")),
                )

            await session.commit()
            out = Path(settings.data_dir) / "visual" / str(sid)
            files = sorted(out.rglob("*.webp"))
            log.info("DONE seconds=%.1f series=%s", time.time() - t0, sid)
            log.info("FILES (%s):", len(files))
            for f in files:
                log.info("  %s (%s bytes)", f, f.stat().st_size)
            print(f"\nSERIES_ID={sid}")
            print(f"OUT_DIR={out}")
        except Exception:
            await session.rollback()
            log.exception("e2e_failed")
            raise


if __name__ == "__main__":
    asyncio.run(main())
