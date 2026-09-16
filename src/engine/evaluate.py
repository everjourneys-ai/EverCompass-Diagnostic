"""
Per-criterion evaluation (Design Spec v1.0 sections 8-9).

Deterministic: score comes straight from the response, classification
comes from a bands lookup already fully defined in the diagnostic
definition (classification_model.bands, i.e. the Maturity Model).
Nothing here is invented -- see DECISIONS.md ADR-010.
"""

from __future__ import annotations

from typing import Optional

from .errors import UnsupportedRuleTypeError
from .types import CriterionResult, Response

#: Rule types this engine build knows how to evaluate. Design Spec
#: section 8 defines five types; every one of the 51 V1 criteria uses
#: `threshold`, so that's all that's implemented. Encountering another
#: type raises rather than silently guessing at behavior no criterion
#: currently exercises (match, conditional, weighted_sum, cross_reference).
IMPLEMENTED_RULE_TYPES = {"threshold"}


def _resolve_bands(definition: dict, bands_ref: str) -> list[dict]:
    section = definition.get(bands_ref)
    if not isinstance(section, dict) or "bands" not in section:
        raise UnsupportedRuleTypeError(
            f"evaluation.rule.bands_ref {bands_ref!r} does not resolve to a "
            f"top-level definition section with a 'bands' list"
        )
    return section["bands"]


def _classify(score: int, bands: list[dict]) -> Optional[str]:
    for band in bands:
        if band["score"] == score:
            return band["classification"]
    return None


def evaluate_criterion(
    criterion_def: dict,
    response: Response,
    definition: dict,
) -> CriterionResult:
    """
    Evaluate one response against its criterion definition.

    Assumes `response` has already passed validate_responses -- this
    function does not re-validate shape, it only scores.
    """
    criterion_id = criterion_def["id"]
    journey_stage = criterion_def["journey_stage"]
    dimension = criterion_def["dimension"]

    rule = criterion_def["evaluation"]["rule"]
    rule_type = rule.get("type")
    if rule_type not in IMPLEMENTED_RULE_TYPES:
        raise UnsupportedRuleTypeError(
            f"criterion {criterion_id!r} uses rule type {rule_type!r}, which "
            f"this engine build does not implement (implemented: "
            f"{sorted(IMPLEMENTED_RULE_TYPES)})"
        )

    if response.applicability == "not_applicable":
        # Design Spec section 7: score = null, classification = null,
        # finding = null, severity = null.
        return CriterionResult(
            criterion_id=criterion_id,
            journey_stage=journey_stage,
            dimension=dimension,
            score=None,
            classification=None,
            finding_id=None,
        )

    bands = _resolve_bands(definition, rule["bands_ref"])
    classification = _classify(response.value, bands)

    return CriterionResult(
        criterion_id=criterion_id,
        journey_stage=journey_stage,
        dimension=dimension,
        score=response.value,
        classification=classification,
        # finding_id is assigned later, once a finding (if any) exists --
        # see findings.py. It is never set here.
        finding_id=None,
    )


def evaluate_all_criteria(
    definition: dict,
    responses: list[Response],
) -> list[CriterionResult]:
    """
    Evaluate every criterion in `definition` against its matching
    response. Callers must run validate_responses() first -- this
    function assumes exactly one response per criterion and does not
    re-check that invariant.
    """
    by_id = {r.criterion_id: r for r in responses}
    return [
        evaluate_criterion(criterion_def, by_id[criterion_def["id"]], definition)
        for criterion_def in definition["criteria"]
    ]
