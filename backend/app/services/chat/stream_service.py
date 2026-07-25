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
    ScriptRepository,
)
from app.schemas.projects.request import ChatMessageRequest
from app.services.chat.activity import ChatAction, ChatPhase, phases_for_action, pick_phrase
from app.services.chat.orchestrator import analyze_user_message, generate_plot_pitches
from app.services.chat.sse import paced_status, sse_event, stream_text_deltas

logger = logging.getLogger(__name__)

DEFAULT_NARRATION = {
    "pov": "third_limited",
    "cast_model": "multicast",
    "platform_style": "pocket_fm_serial",
    "soundscape": True,
    "narrators": [{"id": "NARRATOR", "voice_notes": "intense thriller narrator, measured suspense"}],
}

DEFAULT_EPISODE_DURATION_SEC = 90

_PHASE_HOLD_MS = {
    "thinking": 0,
    "figuring": 700,
    "context": 900,
    "discovering": 0,  # real LLM latency fills this
    "rewriting": 650,
    "writing": 0,
    "polishing": 500,
}


def _infer_action(analysis: dict[str, Any], user_message: str) -> ChatAction:
    explicit = analysis.get("action")
    if explicit in ("chat", "discover", "generate", "rewrite", "context_note"):
        return explicit  # type: ignore[return-value]
    lower = user_message.lower()
    rewrite_hints = ("rewrite", "revise", "redo", "change the script", "update the draft", "fix the script")
    if any(h in lower for h in rewrite_hints):
        return "rewrite"
    context_hints = ("also note", "for context", "remember that", "keep in mind", "add this")
    if any(h in lower for h in context_hints) and "script" not in lower and "write" not in lower:
        return "context_note"
    if analysis.get("plot_pitches"):
        return "discover"
    if analysis.get("intent") != "generate":
        return "chat"
    if not analysis.get("enough_context"):
        return "discover"
    return "generate"


def _soften_reply(reply: str, action: ChatAction) -> str:
    text = (reply or "").strip()
    banned = (
        "source.md", "script writer", "discover context", "discovery",
        "langgraph", "retrieve_context", "build_source",
    )
    lower = text.lower()
    if any(b in lower for b in banned):
        if action == "rewrite":
            return "Got it — I'll rework the script with your notes."
        if action == "generate":
            return "Perfect — starting on your script now. I'll let you know when it's ready."
        if action == "discover":
            return "Here are some directions I'm excited about:"
        if action == "context_note":
            return "Noted — I'll keep that in mind for the next draft."
        return text
    return text


class ChatStreamService:
    def __init__(self, session: AsyncSession, redis: ArqRedis | None) -> None:
        self._session = session
        self._redis = redis
        self._projects = ProjectRepository(session)
        self._attachments = AttachmentRepository(session)
        self._sessions = ChatSessionRepository(session)
        self._runs = RunRepository(session)
        self._scripts = ScriptRepository(session)

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

    async def _emit_phases(
        self,
        phases: list[ChatPhase],
        *,
        action: ChatAction,
        seed: str,
        skip_first: bool = True,
    ) -> AsyncGenerator[dict[str, str], None]:
        start = 1 if skip_first and phases else 0
        for phase in phases[start:]:
            async for evt in paced_status(
                phase=phase,
                label=pick_phrase(phase, seed=f"{seed}:{phase}"),
                action=action,
                hold_ms=_PHASE_HOLD_MS.get(phase, 600),
            ):
                yield evt

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

        async for evt in paced_status(
            phase="thinking",
            label=pick_phrase("thinking", seed=assistant_id),
        ):
            yield evt

        analysis = await analyze_user_message(
            user_message=message,
            history=history,
            attachment_count=len(attachments),
        )
        action = _infer_action(analysis, message)
        phase_plan = phases_for_action(action, has_attachments=has_attachments)

        async for evt in self._emit_phases(phase_plan, action=action, seed=assistant_id):
            yield evt

        reply = _soften_reply(str(analysis.get("reply") or ""), action)

        # ── Discover: pitch plots ─────────────────────────────────────────
        if action == "discover":
            pitches_from_analysis = analysis.get("plot_pitches")

            if pitches_from_analysis and isinstance(pitches_from_analysis, list) and len(pitches_from_analysis) > 0:
                pitches = pitches_from_analysis
            else:
                pitch_result = await generate_plot_pitches(
                    user_message=message,
                    history=history,
                    attachment_count=len(attachments),
                )
                pitches = pitch_result.get("pitches", [])
                if not reply or reply == "Here are some directions I'm excited about:":
                    reply = pitch_result.get("reply", reply)

            content = reply or "Here are 3 story directions — pick one and I'll start writing:"

            async for evt in stream_text_deltas(content):
                yield evt

            yield sse_event({
                "type": "plot_pitches",
                "pitches": pitches,
            })

            _, persisted_id = await append_turn(
                checkpointer,
                session_id=session.id,
                user_text=message,
                assistant_text=content,
                kind="discover",
                questions=[],
                analysis={**analysis, "action": action, "plot_pitches": pitches},
            )
            yield sse_event(
                {
                    "type": "done",
                    "id": persisted_id,
                    "kind": "discover",
                    "content": content,
                    "session_id": session.id,
                    "action": action,
                    "plot_pitches": pitches,
                    "created_at": now.isoformat(),
                }
            )
            return

        # ── Lightweight turns: chat / context_note ────────────────────────
        if action in ("chat", "context_note"):
            kind = "reply"
            content = reply or "How can I help with your story?"
            if action == "context_note":
                content = reply or "Noted — I'll keep that in mind when we write or revise."

            async for evt in stream_text_deltas(content):
                yield evt

            _, persisted_id = await append_turn(
                checkpointer,
                session_id=session.id,
                user_text=message,
                assistant_text=content,
                kind=kind,
                questions=[],
                analysis={**analysis, "action": action},
            )
            yield sse_event(
                {
                    "type": "done",
                    "id": persisted_id,
                    "kind": kind,
                    "content": content,
                    "session_id": session.id,
                    "action": action,
                    "created_at": now.isoformat(),
                }
            )
            return

        # ── generate / rewrite — short intro, then worker run ─────────────
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
        part_number = (await self._scripts.max_part_number(project_id)) + 1

        run = ProjectRun(
            project_id=project_id,
            session_id=session.id,
            prompt=brief,
            status="queued",
            narration_config=DEFAULT_NARRATION,
            part_count=1,
            total_duration_sec=DEFAULT_EPISODE_DURATION_SEC,
            part_number=part_number,
        )
        run = await self._runs.create(run)
        await self._runs.update_status(
            run.id, status=run.status, langgraph_thread_id=run.id
        )
        await self._session.commit()

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
        await self._session.commit()

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

        writing_phase: ChatPhase = "rewriting" if action == "rewrite" else "writing"
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

        async for evt in paced_status(
            phase=writing_phase,
            label=pick_phrase(writing_phase, seed=f"{assistant_id}:run"),
            action=action,
        ):
            yield evt

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
