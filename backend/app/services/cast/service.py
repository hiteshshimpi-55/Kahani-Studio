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


def _parse_sfx_prompt(tags: str | None, description: str | None) -> str | None:
    if tags and "|prompt:" in tags:
        return tags.split("|prompt:", 1)[1].strip() or None
    if description and "ElevenLabs sound effect prompt:" in description:
        # Extract between marker and "When to use:"
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


def hit_to_candidate(rank: int, fields: dict[str, Any]) -> CastCandidate:
    tags = fields.get("tags")
    description = fields.get("description")
    return CastCandidate(
        rank=rank,
        id=fields.get("id"),
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


def _search(query_text: str, *, asset_type: str, num_results: int = 2) -> list[CastCandidate]:
    # Standard endpoint filter syntax from Databricks docs.
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
        # Some responses append score as last anonymous value — already normalized into dict if possible.
        candidates.append(hit_to_candidate(i, fields))
    return candidates


class CastService:
    def recommend(self, script: CastScript) -> CastReport:
        character_results: list[CharacterCastResult] = []
        for ch in script.characters:
            role = (ch.role or "character").lower()
            asset_type = "narrator_voice" if role == "narrator" else "character_voice"
            query = ch.casting_query.strip()
            if script.language:
                query = f"{query}. Language preference: {script.language}."
            if ch.gender:
                query = f"{query} Gender: {ch.gender}."
            if ch.traits:
                query = f"{query} Traits: {', '.join(ch.traits)}."

            # Try role-specific type first; fall back to the other voice type if empty.
            candidates = _search(query, asset_type=asset_type, num_results=2)
            if not candidates:
                alt_type = "character_voice" if asset_type == "narrator_voice" else "narrator_voice"
                candidates = _search(query, asset_type=alt_type, num_results=2)

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
            characters=character_results,
            scenes=scene_results,
            index_name=settings.databricks_cast_index_fqn,
            endpoint_name=settings.databricks_vector_search_endpoint or "",
        )
