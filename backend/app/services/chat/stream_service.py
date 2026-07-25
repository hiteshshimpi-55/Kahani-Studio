"""SSE chat stream — user-facing activity only, no graph node exposure."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.chat_memory import append_turn, load_checkpoint_messages, messages_to_history_pairs
from app.agents.graph.checkpointer import get_checkpointer
from app.errors import AppError
from app.repository.models.project import ChatSession, ProjectRun
from app.repository.projects import (
    AttachmentRepository,
    ChatSessionRepository,
    ProjectRepository,
    RunRepository,
)
from app.schemas.projects.request import ChatMessageRequest, StartRunRequest
from app.services.chat.activity import ChatAction, phases_for_action, pick_phrase
from app.services.chat.orchestrator import analyze_user_message
from app.services.chat.sse import sse_event, stream_text_deltas

logger = logging.getLogger(__name__)

DEFAULT_NARRATION = {
    "pov": "third_limited",
    "cast_model": "multicast",
    "platform_style": "pocket_fm_serial",
    "soundscape": True,
    "narrators": [{"id": "NARRATOR", "voice_notes": "calm thriller guide"}],
}


def _infer_action(analysis: dict[str, Any], user_message: str) -> ChatAction:
    explicit = analysis.get("action")
    if explicit in ("chat", "clarify", "generate", "rewrite", "context_note"):
        return explicit  # type: ignore[return-value]
    lower = user_message.lower()
    rewrite_hints = ("rewrite", "revise", "redo", "change the script", "update the draft", "fix the script")
    if any(h in lower for h in rewrite_hints):
        return "rewrite"
    if analysis.get("intent") != "generate":
        return "clarify" if analysis.get("needs_clarification") else "chat"
    if not analysis.get("enough_context"):
        return "clarify"
    return "generate"


class ChatStreamService:
    def __init__(self, session: AsyncSession, redis: ArqRedis | None) -> None:
        self._session = session
        self._redis = redis
        self._projects = ProjectRepository(session)
        self._attachments = AttachmentRepository(session)
        self._sessions = ChatSessionRepository(session)
        self._runs = RunRepository(session)

    async def _require_project(self, project_id: str):
        row = await self._projects.get(project_id)
        if not row:
            raise AppError(code="NOT_FOUND", message="Project not found", http_status_code=404)
        return row

    async def _ensure_default_session(self, project_id: str) -> ChatSession:
        rows = await self._sessions.list_for_project(project_id)
        if rows:
            return rows[0]
        return await self._sessions.create(
            ChatSession(project_id=project_id, title="Session 1")
        )

    async def stream_message(
        self, project_id: str, body: ChatMessageRequest
    ) -> AsyncGenerator[dict[str, str], None]:
        await self._require_project(project_id)
        if body.session_id:
            session = await self._sessions.get(body.session_id)
            if not session or session.project_id != project_id:
                raise AppError(code="NOT_FOUND", message="Session not found", http_status_code=404)
        else:
            session = await self._ensure_default_session(project_id)

        message = body.message.strip()
        checkpointer = get_checkpointer()
        prior = await load_checkpoint_messages(checkpointer, session.id)
        history = messages_to_history_pairs(prior)
        attachments = await self._attachments.list_for_project(project_id)
        has_attachments = len(attachments) > 0

        assistant_id = str(uuid4())
        now = datetime.now(timezone.utc)

        yield sse_event({"type": "start", "assistant_id": assistant_id, "session_id": session.id})

        yield sse_event(
            {
                "type": "status",
                "phase": "thinking",
                "label": pick_phrase("thinking", seed=assistant_id),
            }
        )

        analysis = await analyze_user_message(
            user_message=message,
            history=history,
            attachment_count=len(attachments),
        )
        action = _infer_action(analysis, message)
        phase_plan = phases_for_action(action, has_attachments=has_attachments)

        for phase in phase_plan[1:]:
            yield sse_event(
                {
                    "type": "status",
                    "phase": phase,
                    "label": pick_phrase(phase, seed=f"{assistant_id}:{phase}"),
                    "action": action,
                }
            )

        questions = analysis.get("questions") or []
        reply = str(analysis.get("reply") or "").strip()

        if action in ("chat", "clarify"):
            kind = "clarify" if action == "clarify" or questions else "reply"
            if questions:
                q_block = "\n".join(f"- {q}" for q in questions)
                content = f"{reply}\n\n{q_block}".strip() if reply else q_block
            else:
                content = reply

            async for evt in stream_text_deltas(content):
                yield evt

            _, persisted_id = await append_turn(
                checkpointer,
                session_id=session.id,
                user_text=message,
                assistant_text=content,
                kind=kind,
                questions=list(questions),
                analysis=analysis,
            )
            yield sse_event(
                {
                    "type": "done",
                    "id": persisted_id,
                    "kind": kind,
                    "content": content,
                    "session_id": session.id,
                    "questions": list(questions),
                    "action": action,
                    "created_at": now.isoformat(),
                }
            )
            return

        # generate / rewrite — stream intro, then start worker run
        if not reply:
            reply = (
                "Starting on your script now — I'll let you know when it's ready."
                if action == "generate"
                else "Reworking the script with your notes."
            )
        content = reply

        async for evt in stream_text_deltas(content):
            yield evt

        brief = str(analysis.get("generation_brief") or message).strip()
        part_count = analysis.get("suggested_part_count") or 4

        run = ProjectRun(
            project_id=project_id,
            session_id=session.id,
            prompt=brief,
            status="queued",
            narration_config=DEFAULT_NARRATION,
            part_count=int(part_count) if part_count else 4,
            total_duration_sec=600,
        )
        run = await self._runs.create(run)
        await self._runs.update_status(
            run.id, status=run.status, langgraph_thread_id=run.id
        )

        if self._redis is None:
            raise AppError(
                code="INTERNAL_ERROR",
                message="Redis unavailable",
                http_status_code=503,
            )
        job = await self._redis.enqueue_job(
            "project_run_job",
            project_id=project_id,
            run_id=run.id,
        )
        job_id = getattr(job, "job_id", None) or str(job)
        await self._runs.update_status(run.id, status="queued", arq_job_id=job_id)

        _, persisted_id = await append_turn(
            checkpointer,
            session_id=session.id,
            user_text=message,
            assistant_text=content,
            kind="generating",
            run_id=run.id,
            questions=[],
            analysis={**analysis, "action": action},
        )

        yield sse_event(
            {
                "type": "run_started",
                "id": persisted_id,
                "run_id": run.id,
                "kind": "generating",
                "content": content,
                "session_id": session.id,
                "action": action,
                "created_at": now.isoformat(),
            }
        )

        yield sse_event({"type": "status", "phase": "writing", "label": pick_phrase("writing")})

        yield sse_event(
            {
                "type": "done",
                "id": persisted_id,
                "kind": "generating",
                "content": content,
                "run_id": run.id,
                "session_id": session.id,
                "action": action,
                "created_at": now.isoformat(),
            }
        )
