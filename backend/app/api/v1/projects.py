from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies.db import get_db
from app.schemas.projects.request import (
    ChatMessageRequest,
    CreateCharacterRequest,
    CreateProjectRequest,
    GenerateScriptAudioRequest,
    PinScriptRequest,
    RejectStageRequest,
    SaveDraftRequest,
    StartRunRequest,
    UpdateCharacterRequest,
    UpdateScriptRequest,
)
from app.schemas.projects.response import (
    AttachmentResponse,
    CharacterResponse,
    ChatHistoryItem,
    ChatMessageResponse,
    ChatSessionResponse,
    ProjectResponse,
    RunResponse,
    ScriptAudioStatusResponse,
    ScriptDetailResponse,
    ScriptLatestResponse,
    ScriptSummaryResponse,
    StoryContextSummaryResponse,
)
from app.schemas.story_analysis.request import StoryAnalysisRequest
from app.schemas.story_analysis.response import StoryAnalysisResponse
from app.services.projects import ProjectsService
from app.services.story_analysis.service import analyze_story as _analyze_story
from app.services.chat.stream_service import ChatStreamService

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


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    await _service(request, db).delete_project(project_id)


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


@router.get("/{project_id}/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[ChatSessionResponse]:
    return await _service(request, db).list_sessions(project_id)


@router.post("/{project_id}/sessions", response_model=ChatSessionResponse)
async def reset_session(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    return await _service(request, db).reset_session(project_id)




@router.post("/{project_id}/chat/messages", response_model=ChatMessageResponse)
async def post_chat_message(
    project_id: str,
    body: ChatMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    return await _service(request, db).post_chat_message(project_id, body)


@router.post("/{project_id}/chat/messages/stream")
async def stream_chat_message(
    project_id: str,
    body: ChatMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """SSE stream: status phases + typewriter text + optional run_started."""

    async def _events():
        svc = ChatStreamService(db, redis=getattr(request.app.state, "redis", None))
        async for evt in svc.stream_message(project_id, body):
            yield evt

    return EventSourceResponse(
        _events(),
        ping=15,
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{project_id}/chat/messages", response_model=list[ChatHistoryItem])
async def list_chat_messages(
    project_id: str,
    request: Request,
    session_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[ChatHistoryItem]:
    return await _service(request, db).list_chat_history(project_id, session_id=session_id)


@router.post("/{project_id}/runs/{run_id}/cancel", response_model=RunResponse)
async def cancel_run(
    project_id: str,
    run_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    return await _service(request, db).cancel_run(project_id, run_id)


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
    session_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[RunResponse]:
    return await _service(request, db).list_runs(project_id, session_id=session_id)


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


@router.post(
    "/{project_id}/runs/{run_id}/stages/{stage}/approve",
    response_model=RunResponse,
)
async def approve_stage(
    project_id: str,
    run_id: str,
    stage: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    return await _service(request, db).approve_stage(project_id, run_id, stage)


@router.post(
    "/{project_id}/runs/{run_id}/stages/{stage}/reject",
    response_model=RunResponse,
)
async def reject_stage(
    project_id: str,
    run_id: str,
    stage: str,
    body: RejectStageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    return await _service(request, db).reject_stage(project_id, run_id, stage, body)


@router.post(
    "/{project_id}/runs/{run_id}/visuals/start",
    response_model=RunResponse,
)
async def start_run_visuals(
    project_id: str,
    run_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """Optional: after audio, build lookbook + scene stills for this run."""
    return await _service(request, db).start_visuals(project_id, run_id)


@router.post(
    "/{project_id}/runs/{run_id}/visuals/skip",
    response_model=RunResponse,
)
async def skip_run_visuals(
    project_id: str,
    run_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """Decline companion visuals and continue the cover/assembly path."""
    return await _service(request, db).skip_visuals(project_id, run_id)


@router.get("/{project_id}/runs/{run_id}/audio/file")
async def get_run_audio_file(
    project_id: str,
    run_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    path = await _service(request, db).get_run_audio_file_path(project_id, run_id)
    return FileResponse(path, media_type="audio/mpeg", filename="episode.mp3")


@router.get("/{project_id}/runs/{run_id}/cover")
async def get_run_cover_file(
    project_id: str,
    run_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    path = await _service(request, db).get_run_cover_file_path(project_id, run_id)
    return FileResponse(path, media_type="image/png", filename="cover.png")


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


@router.post(
    "/{project_id}/scripts/{script_id}/pin",
    response_model=ScriptSummaryResponse,
)
async def pin_script(
    project_id: str,
    script_id: str,
    body: PinScriptRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ScriptSummaryResponse:
    return await _service(request, db).pin_script(project_id, script_id, body)


@router.get("/{project_id}/characters", response_model=list[CharacterResponse])
async def list_characters(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[CharacterResponse]:
    return await _service(request, db).list_characters(project_id)


@router.post("/{project_id}/characters", response_model=CharacterResponse)
async def create_character(
    project_id: str,
    body: CreateCharacterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    return await _service(request, db).create_character(project_id, body)


@router.patch(
    "/{project_id}/characters/{character_id}",
    response_model=CharacterResponse,
)
async def update_character(
    project_id: str,
    character_id: str,
    body: UpdateCharacterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    return await _service(request, db).update_character(project_id, character_id, body)


@router.delete("/{project_id}/characters/{character_id}", status_code=204)
async def delete_character(
    project_id: str,
    character_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    await _service(request, db).delete_character(project_id, character_id)


@router.get(
    "/{project_id}/story-context",
    response_model=StoryContextSummaryResponse,
)
async def story_context_summary(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StoryContextSummaryResponse:
    return await _service(request, db).story_context_summary(project_id)


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


@router.post(
    "/{project_id}/scripts/{script_id}/audio",
    response_model=ScriptAudioStatusResponse,
)
async def generate_script_audio(
    project_id: str,
    script_id: str,
    request: Request,
    body: GenerateScriptAudioRequest = GenerateScriptAudioRequest(),
    db: AsyncSession = Depends(get_db),
) -> ScriptAudioStatusResponse:
    """Enqueue ElevenLabs audiobook render for a saved draft."""
    return await _service(request, db).enqueue_script_audio(project_id, script_id, body)


@router.get(
    "/{project_id}/scripts/{script_id}/audio",
    response_model=ScriptAudioStatusResponse,
)
async def get_script_audio_status(
    project_id: str,
    script_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ScriptAudioStatusResponse:
    return await _service(request, db).get_script_audio_status(project_id, script_id)


@router.get("/{project_id}/scripts/{script_id}/audio/file")
async def get_script_audio_file(
    project_id: str,
    script_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    path = await _service(request, db).get_script_audio_file_path(project_id, script_id)
    return FileResponse(path, media_type="audio/mpeg", filename="episode.mp3")


@router.post("/{project_id}/runs/{run_id}/story-analysis", response_model=StoryAnalysisResponse)
async def story_analysis(
    project_id: str,
    run_id: str,
    body: StoryAnalysisRequest,
) -> StoryAnalysisResponse:
    result = await _analyze_story(body.screenplay_md)
    return StoryAnalysisResponse(**result)
