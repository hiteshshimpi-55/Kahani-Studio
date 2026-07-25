from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.schemas.projects.request import CreateProjectRequest, SaveDraftRequest, StartRunRequest, UpdateScriptRequest
from app.schemas.projects.response import (
    AttachmentResponse,
    ProjectResponse,
    RunResponse,
    ScriptDetailResponse,
    ScriptLatestResponse,
    ScriptSummaryResponse,
)
from app.schemas.story_analysis.request import StoryAnalysisRequest
from app.schemas.story_analysis.response import StoryAnalysisResponse
from app.services.projects import ProjectsService
from app.services.story_analysis.service import analyze_story as _analyze_story

router = APIRouter(prefix="/projects", tags=["projects"])


def _service(request: Request, db: AsyncSession) -> ProjectsService:
    return ProjectsService(db, redis=getattr(request.app.state, "redis", None))


@router.post("", response_model=ProjectResponse)
async def create_project(
    body: CreateProjectRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    return await _service(request, db).create_project(body)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    return await _service(request, db).list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    return await _service(request, db).get_project(project_id)


@router.post("/{project_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(
    project_id: str,
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> AttachmentResponse:
    return await _service(request, db).upload_attachment(project_id, file)


@router.get("/{project_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[AttachmentResponse]:
    return await _service(request, db).list_attachments(project_id)


@router.delete("/{project_id}/attachments/{attachment_id}", status_code=204)
async def delete_attachment(
    project_id: str,
    attachment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    await _service(request, db).delete_attachment(project_id, attachment_id)


@router.post("/{project_id}/runs", response_model=RunResponse)
async def start_run(
    project_id: str,
    body: StartRunRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    return await _service(request, db).start_run(project_id, body)


@router.get("/{project_id}/runs", response_model=list[RunResponse])
async def list_runs(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[RunResponse]:
    return await _service(request, db).list_runs(project_id)


@router.get("/{project_id}/runs/{run_id}", response_model=RunResponse)
async def get_run(
    project_id: str,
    run_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    return await _service(request, db).get_run(project_id, run_id)


@router.post("/{project_id}/runs/{run_id}/draft", response_model=ScriptDetailResponse)
async def save_run_as_draft(
    project_id: str,
    run_id: str,
    request: Request,
    body: SaveDraftRequest = SaveDraftRequest(),
    db: AsyncSession = Depends(get_db),
) -> ScriptDetailResponse:
    return await _service(request, db).save_run_as_draft(project_id, run_id, body)


@router.get("/{project_id}/scripts/latest", response_model=ScriptLatestResponse)
async def latest_script(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ScriptLatestResponse:
    return await _service(request, db).latest_script(project_id)


@router.get("/{project_id}/scripts", response_model=list[ScriptSummaryResponse])
async def list_scripts(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[ScriptSummaryResponse]:
    return await _service(request, db).list_scripts(project_id)


@router.get("/{project_id}/scripts/{script_id}", response_model=ScriptDetailResponse)
async def get_script(
    project_id: str,
    script_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ScriptDetailResponse:
    return await _service(request, db).get_script(project_id, script_id)


@router.patch("/{project_id}/scripts/{script_id}", response_model=ScriptDetailResponse)
async def update_script(
    project_id: str,
    script_id: str,
    body: UpdateScriptRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ScriptDetailResponse:
    return await _service(request, db).update_script(project_id, script_id, body)


@router.post("/{project_id}/runs/{run_id}/story-analysis", response_model=StoryAnalysisResponse)
async def story_analysis(
    project_id: str,
    run_id: str,
    body: StoryAnalysisRequest,
) -> StoryAnalysisResponse:
    result = await _analyze_story(body.screenplay_md)
    return StoryAnalysisResponse(**result)
