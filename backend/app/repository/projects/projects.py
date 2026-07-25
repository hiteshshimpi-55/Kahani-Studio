from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.models.project import (
    ChatSession,
    ChatTurn,
    Project,
    ProjectAttachment,
    ProjectCharacter,
    ProjectRun,
    Script,
)


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, name: str, description: str | None) -> Project:
        row = Project(name=name, description=description)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get(self, project_id: str) -> Project | None:
        return await self._session.get(Project, project_id)

    async def list_all(self) -> list[Project]:
        result = await self._session.execute(
            select(Project).order_by(Project.updated_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, project: Project) -> None:
        await self._session.delete(project)
        await self._session.flush()


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, attachment: ProjectAttachment) -> ProjectAttachment:
        self._session.add(attachment)
        await self._session.flush()
        await self._session.refresh(attachment)
        return attachment

    async def get(self, attachment_id: str) -> ProjectAttachment | None:
        return await self._session.get(ProjectAttachment, attachment_id)

    async def list_for_project(self, project_id: str) -> list[ProjectAttachment]:
        result = await self._session.execute(
            select(ProjectAttachment)
            .where(ProjectAttachment.project_id == project_id)
            .order_by(ProjectAttachment.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, attachment: ProjectAttachment) -> None:
        await self._session.delete(attachment)
        await self._session.flush()

    async def set_index_status(self, attachment_id: str, status: str) -> None:
        row = await self.get(attachment_id)
        if row:
            row.index_status = status
            await self._session.flush()


class ChatSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, session_row: ChatSession) -> ChatSession:
        self._session.add(session_row)
        await self._session.flush()
        await self._session.refresh(session_row)
        return session_row

    async def get(self, session_id: str) -> ChatSession | None:
        return await self._session.get(ChatSession, session_id)

    async def list_for_project(self, project_id: str) -> list[ChatSession]:
        result = await self._session.execute(
            select(ChatSession)
            .where(ChatSession.project_id == project_id)
            .order_by(ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def latest_for_project(self, project_id: str) -> ChatSession | None:
        result = await self._session.execute(
            select(ChatSession)
            .where(ChatSession.project_id == project_id)
            .order_by(ChatSession.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()



class ChatTurnRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, turn: ChatTurn) -> ChatTurn:
        self._session.add(turn)
        await self._session.flush()
        await self._session.refresh(turn)
        return turn

    async def list_for_session(self, session_id: str) -> list[ChatTurn]:
        result = await self._session.execute(
            select(ChatTurn)
            .where(ChatTurn.session_id == session_id)
            .order_by(ChatTurn.created_at.asc())
        )
        return list(result.scalars().all())

    async def update_kind(
        self,
        turn_id: str,
        *,
        kind: str,
        content: str | None = None,
        meta: dict | None = None,
        run_id: str | None = None,
    ) -> ChatTurn | None:
        row = await self._session.get(ChatTurn, turn_id)
        if not row:
            return None
        row.kind = kind
        if content is not None:
            row.content = content
        if meta is not None:
            row.meta = meta
        if run_id is not None:
            row.run_id = run_id
        await self._session.flush()
        await self._session.refresh(row)
        return row


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: ProjectRun) -> ProjectRun:
        self._session.add(run)
        await self._session.flush()
        await self._session.refresh(run)
        return run

    async def get(self, run_id: str) -> ProjectRun | None:
        return await self._session.get(ProjectRun, run_id)

    async def list_for_project(
        self, project_id: str, *, session_id: str | None = None
    ) -> list[ProjectRun]:
        stmt = select(ProjectRun).where(ProjectRun.project_id == project_id)
        if session_id is not None:
            stmt = stmt.where(ProjectRun.session_id == session_id)
        result = await self._session.execute(stmt.order_by(ProjectRun.created_at.asc()))
        return list(result.scalars().all())

    async def assign_orphans(self, project_id: str, session_id: str) -> None:
        await self._session.execute(
            update(ProjectRun)
            .where(
                ProjectRun.project_id == project_id,
                ProjectRun.session_id.is_(None),
            )
            .values(session_id=session_id)
        )
        await self._session.flush()

    async def update_status(
        self,
        run_id: str,
        *,
        status: str,
        error: str | None = None,
        arq_job_id: str | None = None,
        langgraph_thread_id: str | None = None,
    ) -> ProjectRun | None:
        row = await self.get(run_id)
        if not row:
            return None
        row.status = status
        if error is not None:
            row.error = error
        if arq_job_id is not None:
            row.arq_job_id = arq_job_id
        if langgraph_thread_id is not None:
            row.langgraph_thread_id = langgraph_thread_id
        await self._session.flush()
        await self._session.refresh(row)
        return row


class ScriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, script: Script) -> Script:
        self._session.add(script)
        await self._session.flush()
        await self._session.refresh(script)
        return script

    async def latest_for_project(self, project_id: str) -> Script | None:
        result = await self._session.execute(
            select(Script)
            .where(Script.project_id == project_id)
            .order_by(Script.version.desc(), Script.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_for_project(self, project_id: str) -> list[Script]:
        result = await self._session.execute(
            select(Script)
            .where(Script.project_id == project_id)
            .order_by(
                Script.part_number.desc().nulls_last(),
                Script.version.desc(),
                Script.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    async def get(self, script_id: str) -> Script | None:
        return await self._session.get(Script, script_id)

    async def get_for_run(self, run_id: str) -> Script | None:
        result = await self._session.execute(
            select(Script).where(Script.run_id == run_id).limit(1)
        )
        return result.scalar_one_or_none()

    async def next_version(self, project_id: str) -> int:
        latest = await self.latest_for_project(project_id)
        return (latest.version + 1) if latest else 1

    async def max_part_number(self, project_id: str) -> int:
        rows = await self.list_for_project(project_id)
        best = 0
        for script in rows:
            if script.part_number and script.part_number > best:
                best = script.part_number
            else:
                package = script.package_json or {}
                parts = package.get("parts") if isinstance(package, dict) else None
                if isinstance(parts, list) and parts:
                    pn = parts[0].get("part_number") if isinstance(parts[0], dict) else None
                    if isinstance(pn, int) and pn > best:
                        best = pn
        return best

    async def set_pinned(self, script_id: str, pinned: bool) -> Script | None:
        row = await self.get(script_id)
        if not row:
            return None
        row.pinned = pinned
        await self._session.flush()
        await self._session.refresh(row)
        return row


class CharacterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_project(self, project_id: str) -> list[ProjectCharacter]:
        result = await self._session.execute(
            select(ProjectCharacter)
            .where(ProjectCharacter.project_id == project_id)
            .order_by(ProjectCharacter.name.asc())
        )
        return list(result.scalars().all())

    async def get(self, character_id: str) -> ProjectCharacter | None:
        return await self._session.get(ProjectCharacter, character_id)

    async def get_by_key(
        self, project_id: str, character_key: str
    ) -> ProjectCharacter | None:
        result = await self._session.execute(
            select(ProjectCharacter).where(
                ProjectCharacter.project_id == project_id,
                ProjectCharacter.character_key == character_key,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, row: ProjectCharacter) -> ProjectCharacter:
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def delete(self, row: ProjectCharacter) -> None:
        await self._session.delete(row)
        await self._session.flush()

    async def upsert_from_bible(
        self, project_id: str, characters: list[dict]
    ) -> list[ProjectCharacter]:
        """Merge bible.characters into project cast by character_key (or name)."""
        out: list[ProjectCharacter] = []
        for raw in characters:
            if not isinstance(raw, dict):
                continue
            key = str(raw.get("id") or raw.get("character_key") or raw.get("name") or "").strip()
            name = str(raw.get("name") or key).strip()
            if not key or not name:
                continue
            key = key.lower().replace(" ", "_")
            existing = await self.get_by_key(project_id, key)
            if existing:
                existing.name = name
                if raw.get("role") is not None:
                    existing.role = str(raw.get("role") or "") or None
                if raw.get("voice") is not None:
                    existing.voice = str(raw.get("voice") or "") or None
                if raw.get("speech_patterns") is not None:
                    existing.speech_patterns = str(raw.get("speech_patterns") or "") or None
                if raw.get("arc") is not None:
                    existing.arc = str(raw.get("arc") or "") or None
                await self._session.flush()
                await self._session.refresh(existing)
                out.append(existing)
            else:
                row = ProjectCharacter(
                    project_id=project_id,
                    character_key=key,
                    name=name,
                    role=str(raw.get("role") or "") or None,
                    voice=str(raw.get("voice") or "") or None,
                    speech_patterns=str(raw.get("speech_patterns") or "") or None,
                    arc=str(raw.get("arc") or "") or None,
                )
                out.append(await self.create(row))
        return out
