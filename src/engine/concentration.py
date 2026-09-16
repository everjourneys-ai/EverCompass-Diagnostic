"""
Concentration determination (Design Spec v1.0 section 15, Pattern;
priority.scoring_formula.concentration_determination_rule).

DECISION 1 (this session, final for v1.0): semantic related-finding
grouping is DEFERRED. The frozen methodology's own two worked examples
of a Pattern use different axes from each other (one groups by shared
journey_stage, the other by shared dimension) and neither reduces to a
single structural rule without inventing an unstated design choice.
Root-cause/pattern inference is also explicitly deferred to a later
AI-assisted layer elsewhere in the methodology (Design Spec section
18; Architecture v1.2 ADR-008).

For v1.0, every finding is therefore its own isolated group of one:
concentration = "isolated", concentration_weight = 1, unconditionally.
No relatedness is inferred from journey, dimension, criterion type,
impact, severity, proximity, or any combination of these.

This module exists specifically so that boundary is a single, clearly
documented, swappable function rather than scattered through
priority.py. A future diagnostic version that defines real
relationship/pattern data can pass it in via `relationship_rules`
without changing any caller of determine_concentration().
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import Finding


@dataclass(frozen=True)
class ConcentrationResult:
    concentration: str  # "isolated" | "repeated" | "concentrated" | "systemic"
    weight: int
    related_finding_ids: list[str]


def determine_concentration(
    finding: Finding,
    all_findings: list[Finding],
    definition: dict,
    relationship_rules: dict | None = None,
) -> ConcentrationResult:
    """
    v1.0: always isolated/weight=1/related-to-only-itself, per Decision 1.

    `relationship_rules` is the extension point for a future diagnostic
    version: if a definition ever supplies real relationship/pattern
    data (not diagnostic.json v1.0, which deliberately does not), this
    function is where grouping-aware logic would be implemented next --
    the signature already accepts it so no caller needs to change.
    """
    if relationship_rules is not None:
        raise NotImplementedError(
            "relationship_rules is a future extension point -- no diagnostic "
            "version currently supplies one. See Decision 1 (concentration "
            "grouping deferred) -- this is not a bug, it's the documented boundary."
        )

    weights = definition["priority"]["scoring_formula"]["concentration_weights"]
    return ConcentrationResult(
        concentration="isolated",
        weight=weights["isolated"],
        related_finding_ids=[finding.finding_id],
    )
