"""
One application-level operation: resolve which diagnostic definition to
assess against, then run the deterministic engine against it.

    assess_diagnostic(repository, diagnostic_id, diagnostic_version, responses)
        -> engine.types.AssessmentResult

No scoring/aggregation/priority logic lives here -- this function's only
job is resolving (diagnostic_id, diagnostic_version) to a definition
dict and generating the caller-supplied assessment_id the engine
requires (engine.evaluate() deliberately never generates one itself, to
stay a pure function of its inputs -- see src/engine/engine.py). Once
that's done, everything else is a single call into engine.evaluate().
"""

from __future__ import annotations

import uuid

from engine.engine import ENGINE_VERSION, evaluate
from engine.types import AssessmentResult, Response

from .errors import DiagnosticNotFoundError, DiagnosticVersionNotFoundError
from .repository import DiagnosticRepository


def assess_diagnostic(
    repository: DiagnosticRepository,
    diagnostic_id: str,
    diagnostic_version: str,
    responses: list[Response],
) -> AssessmentResult:
    """
    Raises:
        DiagnosticNotFoundError: diagnostic_id is not known to this
            application at all.
        DiagnosticVersionNotFoundError: diagnostic_id is known, but not
            published at diagnostic_version.
        engine.errors.DiagnosticValidationError (or a subclass): the
            response set is invalid against the resolved definition --
            see engine.validate. Not caught here; the API layer maps it.
    """
    if not repository.is_known_id(diagnostic_id):
        raise DiagnosticNotFoundError(diagnostic_id)

    definition = repository.get(diagnostic_id, diagnostic_version)
    if definition is None:
        raise DiagnosticVersionNotFoundError(
            diagnostic_id, diagnostic_version, repository.known_published_versions(diagnostic_id)
        )

    assessment_id = f"asm_{uuid.uuid4().hex}"
    return evaluate(
        definition,
        responses,
        assessment_id=assessment_id,
        diagnostic_version=definition["version"],
        engine_version=ENGINE_VERSION,
    )
