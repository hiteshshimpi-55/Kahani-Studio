import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import constants as c
from app.errors.exceptions import AppError

log = logging.getLogger(__name__)


def install(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_handler)


async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status_code, content=exc.to_dict())


async def _validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [f"{'.'.join(str(x) for x in err.get('loc', []))}: {err.get('msg')}" for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={
            "code": c.ERROR_CODE_VALIDATION,
            "message": c.ERROR_MSG_VALIDATION,
            "details": details,
        },
    )


async def _http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": f"HTTP_{exc.status_code}",
            "message": str(exc.detail),
            "details": [],
        },
    )


async def _unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled_error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": c.ERROR_CODE_INTERNAL,
            "message": c.ERROR_MSG_INTERNAL,
            "details": [],
        },
    )
