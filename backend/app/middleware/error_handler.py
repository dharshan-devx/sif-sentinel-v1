import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import AppError

log = structlog.get_logger()


def error_body(request: Request, code: str, message: str, details: dict | list | None = None) -> dict:
    return {"success": False, "error": {"code": code, "message": message, "details": details or {}}, "request_id": getattr(request.state, "request_id", None)}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=error_body(request, exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Pydantic v2 @field_validator errors include the raw exception object
        # in ctx["error"] which is not JSON-serializable.  Sanitize by
        # converting any non-primitive ctx values to their string form.
        def _safe_errors(errors: list) -> list:
            safe = []
            for err in errors:
                err = dict(err)
                if "ctx" in err:
                    err["ctx"] = {
                        k: str(v) if isinstance(v, Exception) else v
                        for k, v in err["ctx"].items()
                    }
                safe.append(err)
            return safe

        return JSONResponse(
            status_code=422,
            content=error_body(
                request,
                "VALIDATION_ERROR",
                "Request validation failed",
                _safe_errors(exc.errors()),
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        log.exception("database_error", request_id=getattr(request.state, "request_id", None))
        return JSONResponse(status_code=503, content=error_body(request, "DATABASE_ERROR", "Database operation failed"))

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unexpected_error", request_id=getattr(request.state, "request_id", None))
        return JSONResponse(status_code=500, content=error_body(request, "INTERNAL_ERROR", "Unexpected server error"))
