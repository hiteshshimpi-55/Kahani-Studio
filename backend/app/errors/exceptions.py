from app.errors.constants import ERROR_CODE_INTERNAL, ERROR_MSG_INTERNAL


class AppError(Exception):
    def __init__(
        self,
        *,
        code: str = ERROR_CODE_INTERNAL,
        message: str = ERROR_MSG_INTERNAL,
        http_status_code: int = 500,
        details: list[str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.http_status_code = http_status_code
        self.details = details or []
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }
