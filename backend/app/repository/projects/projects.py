from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.models.project import Project, ProjectAttachment, ProjectRun, Script


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

    async def list_for_project(self, project_id: str) -> list[ProjectRun]:
        result = await self._session.execute(
            select(ProjectRun)
            .where(ProjectRun.project_id == project_id)
            .order_by(ProjectRun.created_at.asc())
        )
        return list(result.scalars().all())

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
            .order_by(Script.version.desc(), Script.created_at.desc())
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
