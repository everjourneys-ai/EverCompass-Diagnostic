"""
POST /api/v1/diagnostics/{id}/assess.

This route only: parses the request into engine.types.Response objects,
delegates to application.assessment.assess_diagnostic() for everything
(resolving the diagnostic, validating, evaluating), and serializes the
result. No validation or scoring logic lives here -- request/response
validation errors are raised by application/engine code and turned into
HTTP responses by src/api/error_handlers.py, not caught here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from application.assessment import assess_diagnostic
from application.repository import DiagnosticRepository
from engine.serialize import to_dict
from engine.types import Response

from ..dependencies import get_repository
from ..schemas.responses import AssessRequest
from ..schemas.results import AssessmentResultOut

router = APIRouter(prefix="/api/v1/diagnostics", tags=["assess"])


@router.post("/{diagnostic_id}/assess", response_model=AssessmentResultOut)
async def assess(
    diagnostic_id: str,
    body: AssessRequest,
    repository: DiagnosticRepository = Depends(get_repository),
) -> dict:
    responses = [
        Response(criterion_id=r.criterion_id, value=r.value, evidence=r.evidence, applicability=r.applicability)
        for r in body.responses
    ]
    result = assess_diagnostic(repository, diagnostic_id, body.diagnostic_version, responses)
    return to_dict(result)
