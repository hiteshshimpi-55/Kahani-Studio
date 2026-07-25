"""Databricks AI Search client with local fallback for offline/dev."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.projects.storage import local_chunks_dir

logger = logging.getLogger(__name__)


class AISearchClient:
    """Upsert / delete / search attachment chunks filtered by project_id."""

    def __init__(self) -> None:
        self._configured = bool(
            settings.databricks_host
            and settings.databricks_token
            and settings.databricks_ai_search_endpoint
            and settings.databricks_ai_search_index
        )
        self._index = None
        if self._configured:
            try:
                self._index = self._connect_index()
            except Exception:
                logger.exception("Failed to connect Databricks AI Search; using local store")
                self._configured = False
                self._index = None

    def _connect_index(self) -> Any:
        try:
            from databricks.vector_search.client import VectorSearchClient as Client
        except ImportError:
            try:
                from databricks.ai_search import AISearchClient as Client  # type: ignore
            except ImportError as exc:
                raise RuntimeError("databricks-ai-search not installed") from exc

        client = Client(
            workspace_url=settings.databricks_host,
            personal_access_token=settings.databricks_token,
        )
        return client.get_index(
            endpoint_name=settings.databricks_ai_search_endpoint,
            index_name=settings.databricks_ai_search_index,
        )

    @property
    def using_databricks(self) -> bool:
        return self._configured and self._index is not None

    def upsert_chunks(
        self,
        *,
        project_id: str,
        attachment_id: str,
        filename: str,
        chunks: list[str],
    ) -> None:
        records = [
            {
                "id": f"{attachment_id}_{i}",
                "project_id": project_id,
                "attachment_id": attachment_id,
                "chunk_index": i,
                "text": chunk,
                "filename": filename,
            }
            for i, chunk in enumerate(chunks)
        ]
        if self.using_databricks:
            try:
                self._index.upsert(records)
                return
            except Exception:
                logger.exception("Databricks upsert failed; writing local chunks")

        self._write_local(project_id, attachment_id, records)

    def delete_by_attachment(self, *, project_id: str, attachment_id: str) -> None:
        if self.using_databricks:
            try:
                # Prefer primary-key delete when supported; fall back to filter delete.
                ids = [f"{attachment_id}_{i}" for i in range(500)]
                if hasattr(self._index, "delete"):
                    self._index.delete(ids)
            except Exception:
                logger.exception("Databricks delete failed")
        path = local_chunks_dir(project_id) / f"{attachment_id}.json"
        if path.exists():
            path.unlink()

    def similarity_search(
        self,
        *,
        project_id: str,
        query_text: str,
        top_k: int = 8,
    ) -> list[dict[str, Any]]:
        if self.using_databricks:
            try:
                result = self._index.similarity_search(
                    query_text=query_text,
                    columns=["id", "project_id", "attachment_id", "chunk_index", "text", "filename"],
                    filters={"project_id": project_id},
                    num_results=top_k,
                )
                return self._normalize_search_result(result)
            except Exception:
                logger.exception("Databricks search failed; using local search")

        return self._local_search(project_id, query_text, top_k)

    def _write_local(self, project_id: str, attachment_id: str, records: list[dict]) -> None:
        path = local_chunks_dir(project_id) / f"{attachment_id}.json"
        path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    def _local_search(self, project_id: str, query_text: str, top_k: int) -> list[dict[str, Any]]:
        root = local_chunks_dir(project_id)
        tokens = {t for t in re.findall(r"\w+", query_text.lower()) if len(t) > 2}
        scored: list[tuple[float, dict[str, Any]]] = []
        for path in root.glob("*.json"):
            try:
                records = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for rec in records:
                text = str(rec.get("text", ""))
                lower = text.lower()
                if not tokens:
                    score = 0.1
                else:
                    score = sum(1.0 for t in tokens if t in lower)
                if score > 0:
                    scored.append((score, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    def _normalize_search_result(self, result: Any) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        data = result
        if isinstance(result, dict):
            data = result.get("result", result).get("data_array", result.get("data_array", []))
            columns = result.get("result", result).get("manifest", {}).get("columns") or result.get(
                "columns"
            )
            if columns and data:
                names = [c["name"] if isinstance(c, dict) else str(c) for c in columns]
                for row in data:
                    rows.append(dict(zip(names, row, strict=False)))
                return rows
        if isinstance(result, list):
            return [r if isinstance(r, dict) else {"text": str(r)} for r in result]
        return rows
