"""
Finding generation (Design Spec v1.0 section 10).

STATUS: stubbed. `finding_model.generation_rule` in diagnostic.json is
explicitly "TBD" -- neither source document defines what condition on
a criterion result should produce a Finding, or which type
(issue/opportunity/strength) it becomes. Design Spec section 11 also
rules out the obvious shortcut (deriving severity as a simple function
of score), so there is no safe default to fall back to.

Per the constraint not to invent proprietary scoring logic, this
returns an empty list rather than a guessed heuristic. When
finding_model.generation_rule is filled in, generate_findings() must be
implemented for real -- it will raise loudly if the definition changes
out from under it without a matching code update, rather than silently
keep returning [].
"""

from __future__ import annotations

from dataclasses import replace

from .errors import UndefinedDiagnosticRuleError
from .types import CriterionResult, Finding


def generate_findings(
    definition: dict,
    criterion_results: list[CriterionResult],
) -> list[Finding]:
    rule = definition.get("finding_model", {}).get("generation_rule")
    if rule == "TBD":
        return []
    raise UndefinedDiagnosticRuleError(
        "finding_model.generation_rule is no longer 'TBD' but generate_findings() "
        "has no interpreter for it yet. Update this function to match the newly "
        "defined rule before relying on this definition's findings -- do not "
        "assume the old stub behavior (empty findings) is still correct."
    )


def attach_finding_ids(
    criterion_results: list[CriterionResult],
    findings: list[Finding],
) -> list[CriterionResult]:
    """
    Return a new criterion_results list with finding_id populated for
    any criterion that a finding references. A no-op while findings is
    always [], but written generically so it needs no changes once
    generate_findings() is implemented for real.
    """
    finding_by_criterion = {f.criterion_id: f.finding_id for f in findings}
    return [
        replace(cr, finding_id=finding_by_criterion.get(cr.criterion_id, cr.finding_id))
        for cr in criterion_results
    ]
