"""Helpers for series cast + episode continuity injected into script generation."""

from __future__ import annotations

from typing import Any

from app.repository.models.project import ProjectCharacter, Script


def character_to_dict(row: ProjectCharacter) -> dict[str, Any]:
    return {
        "id": row.character_key,
        "character_key": row.character_key,
        "name": row.name,
        "role": row.role,
        "voice": row.voice,
        "speech_patterns": row.speech_patterns,
        "arc": row.arc,
    }


def package_cliff(package: dict[str, Any] | None) -> str | None:
    if not isinstance(package, dict):
        return None
    parts = package.get("parts")
    if not isinstance(parts, list) or not parts:
        return None
    part = parts[0] if isinstance(parts[0], dict) else {}
    cliff = part.get("cliff_out")
    return str(cliff) if cliff else None


def package_part_number(package: dict[str, Any] | None) -> int | None:
    if not isinstance(package, dict):
        return None
    parts = package.get("parts")
    if not isinstance(parts, list) or not parts:
        return None
    part = parts[0] if isinstance(parts[0], dict) else {}
    pn = part.get("part_number")
    return int(pn) if isinstance(pn, int) else None


def package_title(package: dict[str, Any] | None) -> str | None:
    if not isinstance(package, dict):
        return None
    title = package.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    parts = package.get("parts")
    if isinstance(parts, list) and parts and isinstance(parts[0], dict):
        t = parts[0].get("title")
        if isinstance(t, str) and t.strip():
            return t.strip()
    return None


def screenplay_excerpt(package: dict[str, Any] | None, *, limit: int = 1800) -> str:
    if not isinstance(package, dict):
        return ""
    parts = package.get("parts")
    if not isinstance(parts, list) or not parts:
        return ""
    part = parts[0] if isinstance(parts[0], dict) else {}
    text = str(part.get("screenplay") or "").strip()
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def script_to_continuity(
    script: Script,
    *,
    is_latest: bool = False,
    screenplay_md: str | None = None,
) -> dict[str, Any]:
    package = script.package_json if isinstance(script.package_json, dict) else {}
    part_number = script.part_number or package_part_number(package) or script.version
    excerpt = screenplay_excerpt(package)
    if not excerpt and screenplay_md:
        excerpt = screenplay_md.strip()[:1800]
    return {
        "script_id": script.id,
        "part_number": part_number,
        "title": package_title(package),
        "cliff_out": package_cliff(package),
        "screenplay_excerpt": excerpt,
        "pinned": bool(script.pinned),
        "is_latest": is_latest,
    }


def bible_characters(package: dict[str, Any] | None) -> list[dict]:
    if not isinstance(package, dict):
        return []
    bible = package.get("bible")
    if not isinstance(bible, dict):
        return []
    chars = bible.get("characters")
    return list(chars) if isinstance(chars, list) else []
