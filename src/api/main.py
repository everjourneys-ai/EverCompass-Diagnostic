"""
FastAPI app factory. This module -- and nothing above it in the HTTP ->
application -> engine boundary -- owns HTTP concerns: routing, request
parsing, response serialization, status codes, CORS, and error-shape
translation (src/api/error_handlers.py). It contains no assessment or
scoring methodology; every route delegates to src/application.

Run locally:

    PYTHONPATH=src uvicorn api.main:app --reload

See API.md for the full local-development guide.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from application.repository import DiagnosticRepository

from .config import load_settings
from .error_handlers import register_error_handlers
from .middleware import AccessLogMiddleware
from .routes import assess, diagnostics, health

#: The API's own contract version, independent of ENGINE_VERSION
#: (src/engine/engine.py) and any diagnostic_version -- bumping this
#: reflects a change to the HTTP contract itself.
API_VERSION = "0.1.0"

_DEFAULT_DEFINITION_PATHS = [Path(__file__).resolve().parents[1] / "definitions" / "diagnostic.json"]

logging.basicConfig(level=logging.INFO)


def create_app(definition_paths: list[Path] | None = None) -> FastAPI:
    settings = load_settings()

    app = FastAPI(
        title="EverCompass Diagnostic API",
        description=(
            "Deterministic EverCompass business-diagnostic assessment API. "
            "Wraps the pure Assessment Engine -- see ENGINE_STATUS.md and "
            "DECISIONS.md in the repository for the underlying methodology."
        ),
        version=API_VERSION,
    )

    app.state.repository = DiagnosticRepository(definition_paths or _DEFAULT_DEFINITION_PATHS)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.add_middleware(AccessLogMiddleware)

    register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(diagnostics.router)
    app.include_router(assess.router)

    return app


app = create_app()
