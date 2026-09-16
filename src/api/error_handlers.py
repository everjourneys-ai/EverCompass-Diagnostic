"""
Central mapping from every error this API can raise to the consistent
JSON error shape ({"error": {"code", "message", "details"?}}) and the
right HTTP status code -- so no route handler builds an error response
by hand, and no Python exception (message, type, traceback) ever reaches
a client directly.

Two error families are mapped here, deliberately kept distinct (see
src/application/errors.py's own docstring):
  - application.errors.* (diagnostic id/version not known to this
    application) -> 404.
  - engine.errors.DiagnosticValidationError subclasses (the response set
    itself is invalid against the resolved definition) -> 400, per
    Design Spec section 24 / this task's explicit error-code list.

engine.errors.UnsupportedRuleTypeError / UndefinedDiagnosticRuleError
mean the resolved *definition* itself is unusable -- not something any
caller's request could have avoided -- so they map to 500, logged
server-side, with no detail (not proprietary rule information, but also
not the caller's problem) exposed in the response body. This should
never actually fire against the frozen, fully-resolved v1.0 definition;
it exists so a future broken/partial definition fails loudly server-side
rather than as a confusing 400.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from application.errors import DiagnosticNotFoundError, DiagnosticVersionNotFoundError
from engine.errors import (
    ContradictoryApplicabilityError,
    DuplicateResponseError,
    InvalidValueError,
    MissingResponseError,
    UndefinedDiagnosticRuleError,
    UnknownCriterionError,
    UnknownDiagnosticVersionError,
    UnsupportedRuleTypeError,
)

logger = logging.getLogger("evercompass.api")

#: engine.errors.DiagnosticValidationError subclass -> (error code, HTTP status).
#: UnknownDiagnosticVersionError is included for defense-in-depth only --
#: the application layer resolves the version before the engine ever runs
#: (see src/application/assessment.py), so in practice the engine itself
#: never raises this; if it somehow did, "the version doesn't match what
#: was resolved" is still a 404 case, consistent with the id/version
#: lookup errors above.
_VALIDATION_ERROR_MAP: dict[type[Exception], tuple[str, int]] = {
    MissingResponseError: ("missing_response", status.HTTP_400_BAD_REQUEST),
    UnknownCriterionError: ("unknown_criterion", status.HTTP_400_BAD_REQUEST),
    InvalidValueError: ("invalid_value", status.HTTP_400_BAD_REQUEST),
    DuplicateResponseError: ("duplicate_response", status.HTTP_400_BAD_REQUEST),
    ContradictoryApplicabilityError: ("contradictory_applicability", status.HTTP_400_BAD_REQUEST),
    UnknownDiagnosticVersionError: ("unknown_diagnostic_version", status.HTTP_404_NOT_FOUND),
}

_STATUS_FALLBACK_CODE = {
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
}


def _error_response(status_code: int, code: str, message: str, details: list[str] | None = None) -> JSONResponse:
    body: dict = {"code": code, "message": message}
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content={"error": body})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_malformed_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        field_paths = [".".join(str(p) for p in err["loc"]) for err in exc.errors()]
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            "malformed_request",
            "The request body does not match the expected shape.",
            details=field_paths or None,
        )

    @app.exception_handler(DiagnosticNotFoundError)
    async def handle_diagnostic_not_found(request: Request, exc: DiagnosticNotFoundError) -> JSONResponse:
        return _error_response(status.HTTP_404_NOT_FOUND, "unknown_diagnostic", str(exc))

    @app.exception_handler(DiagnosticVersionNotFoundError)
    async def handle_diagnostic_version_not_found(request: Request, exc: DiagnosticVersionNotFoundError) -> JSONResponse:
        return _error_response(status.HTTP_404_NOT_FOUND, "unknown_diagnostic_version", str(exc))

    for exc_cls, (code, http_status) in _VALIDATION_ERROR_MAP.items():
        async def _handle_validation_error(request: Request, exc, code=code, http_status=http_status) -> JSONResponse:
            return _error_response(http_status, code, str(exc), details=getattr(exc, "details", None) or None)

        app.add_exception_handler(exc_cls, _handle_validation_error)

    async def handle_definition_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Diagnostic definition error while serving %s %s: %s", request.method, request.url.path, exc)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "The server could not process this diagnostic. This has been logged.",
        )

    app.add_exception_handler(UnsupportedRuleTypeError, handle_definition_error)
    app.add_exception_handler(UndefinedDiagnosticRuleError, handle_definition_error)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_FALLBACK_CODE.get(exc.status_code, "http_error")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return _error_response(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception while serving %s %s", request.method, request.url.path)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "An unexpected error occurred. This has been logged.",
        )
