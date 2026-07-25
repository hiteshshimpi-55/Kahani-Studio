"""Seed Unity Catalog cast_assets and create/sync AI Search index.

Usage (from backend/ with venv):
  python -m scripts.seed_cast_catalog              # live ElevenLabs voices (requires API key)
  python -m scripts.seed_cast_catalog --allow-curated  # emergency offline seed (NOT for prod casting)
  python -m scripts.seed_cast_catalog --sarvam-only    # upsert Sarvam Bulbul v3 voices only
"""

from __future__ import annotations

import argparse
import logging

from app.core.config import settings
from app.core.logging import configure_logging
from app.integrations.databricks.indexes import (
    create_or_get_cast_index,
    describe_index,
    sync_cast_index,
    wait_until_online,
)
from app.integrations.databricks.sql import (
    ensure_cast_schema_and_table,
    replace_cast_assets,
    upsert_cast_assets,
)
from app.integrations.elevenlabs.sfx_catalog import curated_sfx_rows
from app.integrations.elevenlabs.shot_templates import curated_shot_template_rows
from app.integrations.elevenlabs.voices import collect_voice_rows
from app.integrations.sarvam.constants import sarvam_voice_rows

configure_logging()
log = logging.getLogger("seed_cast_catalog")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed cast_assets + sync AI Search index")
    parser.add_argument(
        "--allow-curated",
        action="store_true",
        help="Allow curated ElevenLabs voice IDs if live pull fails (unsafe for audiobook casting)",
    )
    parser.add_argument(
        "--free-only",
        action="store_true",
        help="Only index shared voices with free_users_allowed=true",
    )
    parser.add_argument(
        "--skip-index-wait",
        action="store_true",
        help="Replace data and trigger sync but do not wait until ONLINE",
    )
    parser.add_argument(
        "--sfx-only",
        action="store_true",
        help="Skip voices; only replace with SFX prompt catalog (dev)",
    )
    parser.add_argument(
        "--shot-templates-only",
        action="store_true",
        help="Upsert curated cinematic shot templates without replacing voices/SFX",
    )
    parser.add_argument(
        "--sarvam-only",
        action="store_true",
        help="Upsert Sarvam Bulbul v3 voices (does not wipe ElevenLabs / SFX)",
    )
    parser.add_argument(
        "--sfx-upsert",
        action="store_true",
        help="Upsert SFX prompt catalog only (does not wipe voices)",
    )
    args = parser.parse_args(argv)

    # ── SFX-only upsert (drama / ambience prompt pack) ───────────────
    if args.sfx_upsert:
        log.info(
            "seed_sfx_upsert catalog=%s schema=%s index=%s",
            settings.databricks_catalog,
            settings.databricks_schema,
            settings.databricks_cast_index_fqn,
        )
        table = ensure_cast_schema_and_table()
        log.info("table_ready %s", table)
        rows = curated_sfx_rows()
        log.info("upserting_sfx count=%s", len(rows))
        n = upsert_cast_assets(rows)
        log.info("sfx_upserted %s", n)
        create_or_get_cast_index()
        sync_cast_index()
        if args.skip_index_wait:
            log.info("skip_index_wait — sync triggered; check dashboard for ONLINE")
            return 0
        status = wait_until_online(timeout_sec=1800, poll_sec=20)
        log.info("index_online status=%s", status.get("status"))
        log.info("done — SFX catalog upserted into vector DB")
        return 0

    # ── Sarvam-only upsert (preferred path for Hindi voice catalog) ──
    if args.sarvam_only:
        log.info(
            "seed_sarvam_only catalog=%s schema=%s index=%s",
            settings.databricks_catalog,
            settings.databricks_schema,
            settings.databricks_cast_index_fqn,
        )
        table = ensure_cast_schema_and_table()
        log.info("table_ready %s", table)
        rows = sarvam_voice_rows()
        log.info("upserting_sarvam_voices count=%s", len(rows))
        n = upsert_cast_assets(rows)
        log.info("sarvam_voices_upserted %s", n)
        create_or_get_cast_index()
        sync_cast_index()
        if args.skip_index_wait:
            log.info("skip_index_wait — sync triggered; check dashboard for ONLINE")
            return 0
        status = wait_until_online(timeout_sec=1800, poll_sec=20)
        log.info("index_online status=%s", status.get("status"))
        log.info("describe=%s", describe_index().get("status"))
        log.info("done — Sarvam voices indexed (preferred over ElevenLabs for Hindi)")
        return 0

    has_key = bool((settings.elevenlabs_api_key or "").strip())
    if (
        not args.sfx_only
        and not args.shot_templates_only
        and not has_key
        and not args.allow_curated
    ):
        log.error(
            "ELEVENLABS_API_KEY is required. Casting must use live ElevenLabs voice IDs only. "
            "Or use --sarvam-only to seed Sarvam voices."
        )
        return 2

    log.info(
        "seed_start catalog=%s schema=%s endpoint=%s index=%s live_key=%s",
        settings.databricks_catalog,
        settings.databricks_schema,
        settings.databricks_vector_search_endpoint,
        settings.databricks_cast_index_fqn,
        has_key,
    )

    table = ensure_cast_schema_and_table()
    log.info("table_ready %s", table)

    if args.shot_templates_only:
        shots = curated_shot_template_rows()
        log.info("upserting_shot_templates count=%s", len(shots))
        n = upsert_cast_assets(shots)
        log.info("shot_templates_upserted %s", n)
    else:
        if args.sfx_only:
            voices: list = []
            sarvam: list = []
        else:
            voices = collect_voice_rows(
                free_only=args.free_only,
                curated_fallback=args.allow_curated,
            )
            sarvam = sarvam_voice_rows()
        sfx = curated_sfx_rows()
        shots = curated_shot_template_rows()
        # Sarvam first in the list so they land in the catalog; casting
        # still prefers them via provider filter at query time.
        rows = sarvam + voices + sfx + shots
        log.info(
            "rows_prepared sarvam=%s elevenlabs=%s sfx=%s shots=%s total=%s",
            len(sarvam),
            len(voices),
            len(sfx),
            len(shots),
            len(rows),
        )

        if not args.sfx_only and not args.allow_curated:
            if len(voices) < 1000:
                log.error(
                    "Live voice pull too small (%s). Expected ~15k Voice Library IDs. Aborting.",
                    len(voices),
                )
                return 3
            bad = [r for r in voices if not (r.get("provider_id") or "").strip()]
            if bad:
                log.error("voices_missing_provider_id count=%s", len(bad))
                return 4
            narr = sum(1 for r in voices if r.get("asset_type") == "narrator_voice")
            char = sum(1 for r in voices if r.get("asset_type") == "character_voice")
            log.info(
                "voice_type_split sarvam=%s narrator=%s character=%s sfx=%s shots=%s",
                len(sarvam),
                narr,
                char,
                len(sfx),
                len(shots),
            )

        log.info("clearing_and_replacing_cast_assets…")
        n = replace_cast_assets(rows)
        log.info("rows_replaced %s", n)

    create_or_get_cast_index()
    sync_cast_index()
    if args.skip_index_wait:
        log.info("skip_index_wait — sync triggered; check dashboard for ONLINE")
        return 0

    status = wait_until_online(timeout_sec=3600, poll_sec=30)
    log.info("index_online status=%s", status.get("status"))
    log.info("describe=%s", describe_index().get("status"))
    log.info(
        "done — DATABRICKS_VECTOR_SEARCH_INDEX=%s",
        settings.databricks_cast_index_fqn,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log.exception("seed_failed")
        raise SystemExit(1)
