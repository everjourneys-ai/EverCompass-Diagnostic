"""
The Assessment Engine's single public entrypoint (Architecture v1.2
section 3): evaluate(diagnostic_definition, responses) -> Result.

Pure function. No HTTP, no database, no AI call, no clock read or
randomness that affects output -- assessment_id and engine_version are
passed in by the caller rather than generated here, specifically so
the function stays deterministic (same inputs => same output, always).
"""

from __future__ import annotations

from .aggregate import aggregate_dimensions, aggregate_journey_stages
from .evaluate import evaluate_all_criteria
from .findings import attach_finding_ids, generate_findings
from .priority import generate_priorities
from .summary import build_system_summary
from .types import AssessmentResult, Response
from .validate import validate_responses

#: This build's engine version (Architecture v1.2 ADR-006: tracked
#: independently of diagnostic_version -- bumping this never implies a
#: methodology change, and vice versa; only src/definitions/diagnostic.json's
#: own "version" field does that). Response validation, per-criterion
#: evaluation, finding generation, severity derivation, dimension/journey
#: aggregation, concentration, and priority scoring/ordering are all fully
#: implemented against Diagnostic Definition v1.0.0 (69/69 tests passing).
#: Still ahead of this engine, not part of its version: a FastAPI layer,
#: an application layer between FastAPI and this engine, and persistence.
ENGINE_VERSION = "0.2.0"


def evaluate(
    definition: dict,
    responses: list[Response],
    assessment_id: str,
    diagnostic_version: str,
    engine_version: str = ENGINE_VERSION,
) -> AssessmentResult:
    """
    Run one deterministic assessment.

    Args:
        definition: a loaded diagnostic definition dict (the parsed
            contents of diagnostic.json for one pinned version).
        responses: the full response set for this assessment.
        assessment_id: caller-supplied identifier for this assessment.
            Not generated internally -- see module docstring.
        diagnostic_version: the version the caller intended to assess
            against. Validated against definition["version"]; a
            mismatch raises UnknownDiagnosticVersionError rather than
            silently scoring against whatever was loaded.
        engine_version: defaults to this build's ENGINE_VERSION.

    Raises:
        DiagnosticValidationError (or a subclass): the response set is
            invalid -- see errors.py and Design Spec section 24.
        UnsupportedRuleTypeError: a criterion uses a rule type this
            engine build doesn't implement.
    """
    validate_responses(definition, responses, diagnostic_version)

    criterion_results = evaluate_all_criteria(definition, responses)

    findings = generate_findings(definition, criterion_results)
    criterion_results = attach_finding_ids(criterion_results, findings)

    dimensions = aggregate_dimensions(definition, criterion_results, findings)
    journey_stages = aggregate_journey_stages(definition, criterion_results, findings)

    priorities = generate_priorities(definition, findings)

    system_summary = build_system_summary(definition, criterion_results, findings, priorities)

    return AssessmentResult(
        assessment_id=assessment_id,
        diagnostic_id=definition["diagnostic_id"],
        diagnostic_version=definition["version"],
        engine_version=engine_version,
        criterion_results=criterion_results,
        findings=findings,
        dimensions=dimensions,
        journey_stages=journey_stages,
        priorities=priorities,
        system_summary=system_summary,
    )
