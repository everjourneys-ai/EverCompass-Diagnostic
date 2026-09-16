"""FastAPI dependency providers. The DiagnosticRepository is built once
at app startup (src/api/main.py::create_app) and stored on app.state --
routes borrow it per-request rather than re-reading definition files off
disk on every call."""

from __future__ import annotations

from fastapi import Request

from application.repository import DiagnosticRepository


def get_repository(request: Request) -> DiagnosticRepository:
    return request.app.state.repository
