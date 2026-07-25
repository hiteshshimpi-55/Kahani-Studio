"""Fetch ElevenLabs voices and normalize to cast_assets rows."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.integrations.elevenlabs.client import get_elevenlabs_client
from app.integrations.elevenlabs.curated_voices import curated_voice_rows

log = logging.getLogger(__name__)

# Shared library page_size max is 100 per ElevenLabs API docs.
_SHARED_PAGE_SIZE = 100
# Safety cap (~50k voices) so a runaway loop cannot hang forever.
_MAX_SHARED_PAGES = 500


def _labels(voice: Any) -> dict[str, str]:
    raw = getattr(voice, "labels", None) or {}
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items() if v is not None}
    return {}


def _build_description(
    *,
    name: str,
    language: str,
    gender: str,
    age: str,
    accent: str,
    use_case: str,
    descriptive: str,
    extra: str,
    voice_id: str,
    category: str = "",
    locale: str = "",
    source: str = "voice_library",
    api_note: str = "",
) -> str:
    parts = [
        f"Character / narrator voice: {name}.",
        extra.strip(),
        f"Language: {language}.",
        f"Locale: {locale}." if locale else "",
        f"Gender: {gender}. Age: {age}. Accent: {accent}.",
        f"Primary use case: {use_case}. Tone / descriptive labels: {descriptive}.",
        f"Voice category: {category}." if category else "",
        f"Source: {source}.",
        api_note,
        f"ElevenLabs voice_id={voice_id}.",
        (
            "Casting fit: audiobook narration, Pocket FM / serial audio drama, "
            "Hindi or English character dialogue, thriller horror romance drama roles, "
            "background character lines, and lead protagonist or antagonist speech."
        ),
    ]
    return " ".join(p for p in parts if p)


def _infer_asset_type(use_case: str, descriptive: str = "") -> str:
    blob = f"{use_case} {descriptive}".lower()
    if any(k in blob for k in ("narrat", "audiobook", "storytell", "news", "documentary")):
        return "narrator_voice"
    return "character_voice"


def _row_from_shared(v: Any, now: str, *, free_only: bool = False) -> dict[str, Any] | None:
    voice_id = getattr(v, "voice_id", None) or getattr(v, "voiceId", None)
    if not voice_id:
        return None

    free_ok = getattr(v, "free_users_allowed", None)
    if free_ok is None:
        free_ok = True
    free_ok = bool(free_ok)
    if free_only and not free_ok:
        return None

    name = getattr(v, "name", None) or "Unknown"
    gender = (getattr(v, "gender", None) or "unknown").lower()
    age = (getattr(v, "age", None) or "unknown").lower()
    accent = (getattr(v, "accent", None) or "unknown").lower()
    language = (getattr(v, "language", None) or "en").lower()
    locale = (getattr(v, "locale", None) or "") or ""
    use_case = (getattr(v, "use_case", None) or "narration").lower()
    descriptive = getattr(v, "descriptive", None) or ""
    description_api = getattr(v, "description", None) or ""
    preview = getattr(v, "preview_url", None)
    category = str(getattr(v, "category", None) or "")

    asset_type = _infer_asset_type(use_case, descriptive)
    blurb = description_api or descriptive or f"{name} voice for {use_case}"
    description = _build_description(
        name=name,
        language=language,
        gender=gender,
        age=age,
        accent=accent,
        use_case=use_case,
        descriptive=descriptive or "n/a",
        extra=blurb,
        voice_id=voice_id,
        category=category,
        locale=str(locale),
        source="elevenlabs_shared_voice_library",
        api_note=(
            "Listed in ElevenLabs community Voice Library. "
            "Web free_users_allowed="
            + ("true" if free_ok else "false")
            + ". API TTS may require a paid ElevenLabs plan for library voices."
        ),
    )
    # One row per voice_id (library identity), language kept as metadata.
    return {
        "id": f"voice_{voice_id}",
        "asset_type": asset_type,
        "provider": "elevenlabs",
        "provider_id": voice_id,
        "name": name,
        "language": language,
        "gender": gender,
        "age": age,
        "accent": accent,
        "use_case": use_case,
        "free_users_allowed": free_ok,
        "preview_url": preview,
        "tags": ",".join(
            x
            for x in [
                language,
                gender,
                age,
                accent,
                use_case,
                descriptive,
                category,
                "voice_library",
                "free" if free_ok else "paid_only",
                asset_type,
            ]
            if x
        ),
        "description": description,
        "updated_at": now,
    }


def fetch_all_shared_voices(
    *,
    page_size: int = _SHARED_PAGE_SIZE,
    free_only: bool = False,
) -> list[dict[str, Any]]:
    """Paginate GET /v1/shared-voices until exhausted (full Voice Library)."""
    if not (settings.elevenlabs_api_key or "").strip():
        log.warning("elevenlabs_api_key_missing — cannot pull Voice Library")
        return []

    client = get_elevenlabs_client()
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    page = 0
    total_reported: int | None = None

    while page < _MAX_SHARED_PAGES:
        try:
            # created_date is the API default and the safest sort for full enumeration.
            resp = client.voices.get_shared(
                page_size=page_size,
                page=page,
                sort="created_date",
            )
        except TypeError:
            # Older SDK kw names
            resp = client.voices.get_shared(
                page_size=page_size,
                page=page,
            )
        except Exception as exc:
            log.error("get_shared_failed page=%s err=%s", page, exc)
            break

        if total_reported is None:
            total_reported = getattr(resp, "total_count", None)
            if total_reported:
                log.info("shared_voices_total_count=%s", total_reported)

        voices = getattr(resp, "voices", None) or []
        if not voices:
            break

        for v in voices:
            row = _row_from_shared(v, now, free_only=free_only)
            if not row or row["id"] in seen:
                continue
            seen.add(row["id"])
            rows.append(row)

        log.info(
            "shared_voices_page=%s fetched=%s unique_total=%s has_more=%s",
            page,
            len(voices),
            len(rows),
            getattr(resp, "has_more", None),
        )
        if not getattr(resp, "has_more", False):
            break
        page += 1

    log.info("shared_voices_done unique=%s pages=%s", len(rows), page + 1)
    return rows


def fetch_account_voices() -> list[dict[str, Any]]:
    """Account / premade voices available to this API key (GET /v2/voices search)."""
    if not (settings.elevenlabs_api_key or "").strip():
        return []

    client = get_elevenlabs_client()
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    next_token: str | None = None

    for _ in range(50):
        try:
            kwargs: dict[str, Any] = {"page_size": 100}
            if next_token:
                kwargs["next_page_token"] = next_token
            resp = client.voices.search(**kwargs)
        except Exception as exc:
            log.warning("voices_search_failed err=%s", exc)
            break

        voices = getattr(resp, "voices", None) or []
        for v in voices:
            labels = _labels(v)
            voice_id = getattr(v, "voice_id", None)
            if not voice_id or voice_id in seen:
                continue
            seen.add(voice_id)
            language = (labels.get("language") or "en").lower()
            gender = (labels.get("gender") or "unknown").lower()
            age = (labels.get("age") or "unknown").lower()
            accent = (labels.get("accent") or "unknown").lower()
            use_case = (labels.get("use_case") or labels.get("descriptive") or "narration").lower()
            name = getattr(v, "name", None) or "Voice"
            category = str(getattr(v, "category", None) or "")
            asset_type = _infer_asset_type(use_case, labels.get("description", ""))
            is_premade = category.lower() == "premade"
            api_note = (
                "Premade default voice in this account — verified usable for free-tier API TTS."
                if is_premade
                else "In this account's voice collection. Library/shared voices need a paid plan for API TTS."
            )
            label_tags = ",".join(f"{k}:{val}" for k, val in labels.items())
            rows.append(
                {
                    "id": f"voice_{voice_id}",
                    "asset_type": asset_type,
                    "provider": "elevenlabs",
                    "provider_id": voice_id,
                    "name": name,
                    "language": language,
                    "gender": gender,
                    "age": age,
                    "accent": accent,
                    "use_case": use_case,
                    "free_users_allowed": True,
                    "preview_url": getattr(v, "preview_url", None),
                    "tags": ",".join(
                        x
                        for x in [
                            label_tags,
                            "account",
                            category,
                            "api_tts_free" if is_premade else "api_tts_paid_required",
                            asset_type,
                        ]
                        if x
                    ),
                    "description": _build_description(
                        name=name,
                        language=language,
                        gender=gender,
                        age=age,
                        accent=accent,
                        use_case=use_case,
                        descriptive=labels.get("description", "account voice"),
                        extra=getattr(v, "description", None) or f"{name} account voice",
                        voice_id=voice_id,
                        category=category,
                        source="elevenlabs_account_voices",
                        api_note=api_note,
                    ),
                    "updated_at": now,
                }
            )

        if not getattr(resp, "has_more", False):
            break
        next_token = getattr(resp, "next_page_token", None)
        if not next_token:
            break

    log.info("account_voices_done unique=%s", len(rows))
    return rows


def fetch_live_voice_rows(*, free_only: bool = False) -> list[dict[str, Any]]:
    """Full live pull: entire shared library + account voices."""
    shared = fetch_all_shared_voices(free_only=free_only)
    account = fetch_account_voices()
    by_id = {r["id"]: r for r in shared}
    for r in account:
        existing = by_id.get(r["id"])
        if existing is None:
            by_id[r["id"]] = r
            continue
        # Keep shared metadata; append account usability tags for casting filters.
        tags = (existing.get("tags") or "") + "," + (r.get("tags") or "")
        existing["tags"] = tags.strip(",")
        if "api_tts_free" in (r.get("tags") or ""):
            desc = existing.get("description") or ""
            if "api_tts_free" not in desc:
                existing["description"] = (
                    desc
                    + " Also present as a premade/account voice usable for free-tier API TTS."
                )
            by_id[r["id"]] = existing
        else:
            by_id[r["id"]] = existing
    return list(by_id.values())


def collect_voice_rows(*, free_only: bool = False, curated_fallback: bool = False) -> list[dict[str, Any]]:
    """Live Voice Library + account voices only.

    curated_fallback is off by default: audiobook casting must never recommend a
    voice_id that was not returned by ElevenLabs (stale curated IDs break TTS).
    """
    live = fetch_live_voice_rows(free_only=free_only)
    if live:
        log.info("using_live_voices count=%s", len(live))
        return live
    if curated_fallback:
        log.warning(
            "curated_fallback_enabled — voice IDs may be stale; do not use for production casting"
        )
        curated = curated_voice_rows()
        normalized = []
        for r in curated:
            r = dict(r)
            pid = r.get("provider_id")
            if pid:
                r["id"] = f"voice_{pid}"
            normalized.append(r)
        by_id = {r["id"]: r for r in normalized}
        log.info("using_curated_voices count=%s", len(by_id))
        return list(by_id.values())
    return []
