"""
GET /api/v1/diagnostics, GET /api/v1/diagnostics/{id}.

Both routes only call into application.public_view -- no shaping of the
public projection happens here, so the boundary between "public
diagnostic content" and "internal diagnostic definition" lives in one
place (src/application/public_view.py), not duplicated across routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from application.errors import DiagnosticNotFoundError
from application.public_view import build_diagnostic_summary, build_public_diagnostic
from application.repository import DiagnosticRepository

from ..dependencies import get_repository
from ..schemas.diagnostics import DiagnosticPublicOut, DiagnosticSummaryOut

router = APIRouter(prefix="/api/v1/diagnostics", tags=["diagnostics"])


@router.get("", response_model=list[DiagnosticSummaryOut])
async def list_diagnostics(
    repository: DiagnosticRepository = Depends(get_repository),
) -> list[dict]:
    return [build_diagnostic_summary(definition) for definition in repository.list_published()]


@router.get("/{diagnostic_id}", response_model=DiagnosticPublicOut)
async def get_diagnostic(
    diagnostic_id: str,
    repository: DiagnosticRepository = Depends(get_repository),
) -> dict:
    definition = repository.get(diagnostic_id)
    if definition is None:
        raise DiagnosticNotFoundError(diagnostic_id)
    return build_public_diagnostic(definition)
