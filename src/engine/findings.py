"""
Finding generation (Design Spec v1.0 section 10) and severity
assignment (section 11), both now resolved as declarative data in the
frozen diagnostic.json:

- finding_model.generation_rule: a classification_mapping
  (classification -> finding type). Generic interpreter, dispatches on
  rule["type"] -- adding a new generation_rule type later needs a new
  branch here, not a rewrite.
- severity_model.derivation_rule: a classification_impact_matrix
  (classification x criteria[*].impact -> severity, or null = "NONE").
  Also a generic interpreter.

Neither function hardcodes anything EverCompass-specific (no
`if criterion_id == "..."`) -- both read entirely from `definition`.
"""

from __future__ import annotations

from dataclasses import replace

from .errors import UndefinedDiagnosticRuleError, UnsupportedRuleTypeError
from .types import CriterionResult, Finding

BY_ID_CACHE_KEY = "_by_id"  # not stored on definition; see _criteria_by_id


def _criteria_by_id(definition: dict) -> dict[str, dict]:
    return {c["id"]: c for c in definition["criteria"]}


def _apply_classification_mapping(rule: dict, classification: str) -> str:
    if rule["type"] != "classification_mapping":
        raise UnsupportedRuleTypeError(
            f"finding_model.generation_rule.type {rule['type']!r} is not implemented "
            f"(implemented: classification_mapping)"
        )
    return rule["mapping"][classification]


def _apply_classification_impact_matrix(rule: dict, classification: str, impact: str) -> str | None:
    if rule["type"] != "classification_impact_matrix":
        raise UnsupportedRuleTypeError(
            f"severity_model.derivation_rule.type {rule['type']!r} is not implemented "
            f"(implemented: classification_impact_matrix)"
        )
    return rule["matrix"][classification][impact]


def generate_findings(
    definition: dict,
    criterion_results: list[CriterionResult],
) -> list[Finding]:
    """
    One Finding per applicable criterion (not_applicable criteria
    produce none, per applicability_model.effect_of_not_applicable and
    finding_model.generation_rule.not_applicable_result). finding_id is
    assigned sequentially in criterion_results order, which is itself
    definition["criteria"]'s fixed order -- deterministic.
    """
    gen_rule = definition["finding_model"]["generation_rule"]
    sev_rule = definition["severity_model"]["derivation_rule"]

    if gen_rule == "TBD" or sev_rule == "TBD":
        # Should not happen against a frozen (published) definition, but
        # a caller could in principle hand us an older/draft one.
        raise UndefinedDiagnosticRuleError(
            "finding_model.generation_rule / severity_model.derivation_rule is "
            "still \"TBD\" in this definition -- cannot generate findings."
        )

    by_id = _criteria_by_id(definition)
    findings: list[Finding] = []
    n = 0
    for cr in criterion_results:
        if cr.classification is None:
            continue  # not_applicable -> no finding

        n += 1
        finding_type = _apply_classification_mapping(gen_rule, cr.classification)

        if finding_type == "issue":
            impact = by_id[cr.criterion_id]["impact"]
            severity = _apply_classification_impact_matrix(sev_rule, cr.classification, impact)
        else:
            # Severity describes weaknesses; strength/opportunity findings
            # carry none (matches the matrix's "NONE" rows for
            # strong/operationalized regardless of impact).
            severity = None

        findings.append(Finding(
            finding_id=f"F-{n:03d}",
            criterion_id=cr.criterion_id,
            journey_stage=cr.journey_stage,
            dimension=cr.dimension,
            type=finding_type,
            severity=severity,
        ))
    return findings


def attach_finding_ids(
    criterion_results: list[CriterionResult],
    findings: list[Finding],
) -> list[CriterionResult]:
    """Return a new criterion_results list with finding_id populated for
    any criterion a finding references."""
    finding_by_criterion = {f.criterion_id: f.finding_id for f in findings}
    return [
        replace(cr, finding_id=finding_by_criterion.get(cr.criterion_id, cr.finding_id))
        for cr in criterion_results
    ]
