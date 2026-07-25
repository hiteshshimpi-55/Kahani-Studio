from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.integrations.databricks.vector_search import VectorSearchQuery, similarity_search
from app.schemas.cast.request import CastScript
from app.schemas.cast.response import (
    CastCandidate,
    CastReport,
    CharacterCastResult,
    SceneSfxResult,
)

CAST_COLUMNS = [
    "id",
    "asset_type",
    "provider_id",
    "name",
    "language",
    "gender",
    "description",
    "preview_url",
    "free_users_allowed",
    "tags",
]

# ElevenLabs v3 as primary TTS; Sarvam available as alternative.
PRIMARY_VOICE_PROVIDER = "elevenlabs"
FALLBACK_VOICE_PROVIDER = "sarvam"


def _parse_sfx_prompt(tags: str | None, description: str | None) -> str | None:
    if tags and "|prompt:" in tags:
        return tags.split("|prompt:", 1)[1].strip() or None
    if description and "ElevenLabs sound effect prompt:" in description:
        part = description.split("ElevenLabs sound effect prompt:", 1)[1]
        if "When to use:" in part:
            part = part.split("When to use:", 1)[0]
        return part.strip() or None
    return None


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "1", "yes"}
    return bool(value)


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _infer_provider(fields: dict[str, Any]) -> str | None:
    provider = fields.get("provider")
    if provider:
        return str(provider).strip().lower() or None
    row_id = str(fields.get("id") or "")
    tags = str(fields.get("tags") or "")
    desc = str(fields.get("description") or "")
    if (
        row_id.startswith("sarvam_")
        or "sarvam" in tags.lower()
        or "Provider: sarvam" in desc
        or "Bulbul v3" in desc
    ):
        return "sarvam"
    if row_id.startswith("voice_") or "elevenlabs" in tags.lower() or "ElevenLabs" in desc:
        return "elevenlabs"
    return None


def hit_to_candidate(rank: int, fields: dict[str, Any]) -> CastCandidate:
    tags = fields.get("tags")
    description = fields.get("description")
    return CastCandidate(
        rank=rank,
        id=fields.get("id"),
        provider=_infer_provider(fields),
        provider_id=fields.get("provider_id"),
        name=fields.get("name"),
        asset_type=fields.get("asset_type"),
        language=fields.get("language"),
        gender=fields.get("gender"),
        preview_url=fields.get("preview_url"),
        free_users_allowed=_as_bool(fields.get("free_users_allowed")),
        description=description,
        sfx_prompt=_parse_sfx_prompt(
            str(tags) if tags is not None else None,
            str(description) if description is not None else None,
        ),
        score=_as_float(fields.get("score") or fields.get("similarity")),
        raw=fields,
    )


def _search(
    query_text: str,
    *,
    asset_type: str,
    num_results: int = 8,
) -> list[CastCandidate]:
    """Vector search by asset_type. Provider preference is applied after ranking."""
    filters: dict[str, Any] = {"asset_type": asset_type}
    result = similarity_search(
        VectorSearchQuery(
            query_text=query_text,
            columns=CAST_COLUMNS,
            num_results=num_results,
            filters=filters,
            query_type="ANN",
            endpoint_name=settings.databricks_vector_search_endpoint,
            index_name=settings.databricks_cast_index_fqn,
        )
    )
    candidates: list[CastCandidate] = []
    for i, hit in enumerate(result.hits, start=1):
        fields = dict(hit.raw)
        candidates.append(hit_to_candidate(i, fields))
    return candidates


def _normalize_voice_provider(value: str | None) -> str:
    raw = (value or settings.tts_provider or "elevenlabs").strip().lower()
    if raw in ("elevenlabs", "11labs", "eleven", "el"):
        return FALLBACK_VOICE_PROVIDER
    return PRIMARY_VOICE_PROVIDER


def _dedupe_candidates(candidates: list[CastCandidate]) -> list[CastCandidate]:
    seen: set[str] = set()
    out: list[CastCandidate] = []
    for c in candidates:
        key = (c.provider_id or c.id or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(c)
    for i, c in enumerate(out, start=1):
        c.rank = i
    return out


def _filter_by_provider(
    candidates: list[CastCandidate],
    voice_provider: str,
) -> list[CastCandidate]:
    """Keep only the requested provider. Infer provider from id/tags when needed."""
    locked = _normalize_voice_provider(voice_provider)
    matched = [c for c in candidates if (c.provider or "") == locked]
    return _dedupe_candidates(matched)


def _search_voices(
    query: str,
    *,
    asset_type: str,
    voice_provider: str = "elevenlabs",
) -> list[CastCandidate]:
    """Search cast catalog locked to one voice provider."""
    locked = _normalize_voice_provider(voice_provider)
    if locked == PRIMARY_VOICE_PROVIDER:
        biased = (
            f"{query} Sarvam Bulbul v3 native Indian Hindi voice. "
            f"Provider: sarvam. Speaker from Sarvam catalog."
        )
    else:
        biased = (
            f"{query} ElevenLabs multilingual audiobook voice. "
            f"Provider: elevenlabs. ElevenLabs voice_id."
        )

    raw = _search(biased, asset_type=asset_type, num_results=12)
    candidates = _filter_by_provider(raw, locked)
    if candidates:
        return candidates[:3]

    # Alternate asset type (narrator ↔ character), still locked to provider
    alt_type = "character_voice" if asset_type == "narrator_voice" else "narrator_voice"
    raw = _search(biased, asset_type=alt_type, num_results=12)
    return _filter_by_provider(raw, locked)[:3]


class CastService:
    def recommend(self, script: CastScript) -> CastReport:
        voice_provider = _normalize_voice_provider(script.voice_provider)
        character_results: list[CharacterCastResult] = []
        for ch in script.characters:
            role = (ch.role or "character").lower()
            asset_type = "narrator_voice" if role in ("narrator", "guide") else "character_voice"
            query = ch.casting_query.strip()
            if script.language:
                query = f"{query}. Language preference: {script.language}."
            if voice_provider == PRIMARY_VOICE_PROVIDER:
                query = f"{query} Prefer Sarvam Bulbul v3 native Indian voices."
            else:
                query = f"{query} Prefer ElevenLabs library voices."
            if ch.gender:
                query = f"{query} Gender: {ch.gender}."
            if ch.traits:
                query = f"{query} Traits: {', '.join(ch.traits)}."

            candidates = _search_voices(
                query, asset_type=asset_type, voice_provider=voice_provider,
            )

            character_results.append(
                CharacterCastResult(
                    character_id=ch.id,
                    role=role,
                    query=query,
                    primary=candidates[0] if candidates else None,
                    alternatives=candidates[1:],
                )
            )

        scene_results: list[SceneSfxResult] = []
        for scene in script.scenes:
            query = scene.sfx_query.strip()
            if scene.setting:
                query = f"{query}. Setting: {scene.setting}."
            # SFX remains ElevenLabs sound-generation catalog regardless of TTS provider
            candidates = _search(query, asset_type="sfx", num_results=2)
            scene_results.append(
                SceneSfxResult(
                    scene_id=scene.scene_id,
                    query=query,
                    primary=candidates[0] if candidates else None,
                    alternatives=candidates[1:],
                )
            )

        return CastReport(
            series_id=script.series_id,
            language=script.language,
            voice_provider=voice_provider,
            characters=character_results,
            scenes=scene_results,
            index_name=settings.databricks_cast_index_fqn,
            endpoint_name=settings.databricks_vector_search_endpoint or "",
        )
