"""ARQ worker jobs for indexing and project LangGraph runs."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from app.agents.graph.graph import run_project_graph
from app.core.db.session import AsyncSessionLocal
from app.integrations.databricks_ai_search import AISearchClient
from app.repository.projects import AttachmentRepository, RunRepository
from app.services.projects.chunking import chunk_text
from app.services.projects.storage import runs_dir

logger = logging.getLogger(__name__)


async def index_attachment_job(ctx: dict, project_id: str, attachment_id: str) -> dict:
    async with AsyncSessionLocal() as session:
        repo = AttachmentRepository(session)
        row = await repo.get(attachment_id)
        if not row or row.project_id != project_id:
            return {"ok": False, "error": "attachment not found"}
        try:
            text = Path(row.storage_path).read_text(encoding="utf-8", errors="ignore")
            chunks = chunk_text(text)
            client = AISearchClient()
            client.upsert_chunks(
                project_id=project_id,
                attachment_id=attachment_id,
                filename=row.filename,
                chunks=chunks,
            )
            row.index_status = "indexed"
            await session.commit()
            return {"ok": True, "chunks": len(chunks)}
        except Exception as exc:
            logger.exception("index_attachment_job failed")
            row.index_status = "failed"
            await session.commit()
            return {"ok": False, "error": str(exc)}


async def delete_attachment_index_job(ctx: dict, project_id: str, attachment_id: str) -> dict:
    try:
        client = AISearchClient()
        client.delete_by_attachment(project_id=project_id, attachment_id=attachment_id)
        return {"ok": True}
    except Exception as exc:
        logger.exception("delete_attachment_index_job failed")
        return {"ok": False, "error": str(exc)}


async def project_run_job(ctx: dict, project_id: str, run_id: str) -> dict:
    async with AsyncSessionLocal() as session:
        runs = RunRepository(session)
        run = await runs.get(run_id)
        if not run or run.project_id != project_id:
            return {"ok": False, "error": "run not found"}

        await runs.update_status(run_id, status="running")
        await session.commit()

        try:
            initial = {
                "project_id": project_id,
                "run_id": run_id,
                "prompt": run.prompt,
                "narration_config": run.narration_config or {},
                "part_count": run.part_count or 4,
                "total_duration_sec": run.total_duration_sec or 600,
                "retrieved_chunks": [],
                "source_md": "",
                "script_package": None,
                "screenplay_md": None,
                "errors": [],
            }
            result = await run_project_graph(initial)

            package = result.get("script_package") or {}
            screenplay = result.get("screenplay_md") or ""
            out_dir = runs_dir(project_id, run_id)

            # Persist run artifacts only — drafts are saved explicitly from chat.
            (out_dir / "script.json").write_text(
                json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (out_dir / "screenplay.md").write_text(screenplay, encoding="utf-8")

            await runs.update_status(run_id, status="succeeded", error=None)
            await session.commit()
            return {"ok": True}
        except Exception as exc:
            logger.exception("project_run_job failed")
            await session.rollback()
            async with AsyncSessionLocal() as session2:
                runs2 = RunRepository(session2)
                await runs2.update_status(run_id, status="failed", error=str(exc)[:2000])
                await session2.commit()
            return {"ok": False, "error": str(exc)}
