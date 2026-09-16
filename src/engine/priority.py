"""
Priority generation and ordering (Design Spec v1.0 sections 16-18).

Two genuinely different operations live here, and only one of them is
actually defined:

1. IDENTIFYING priorities -- grouping related findings into a named
   Priority in the first place. This needs pattern/concentration
   detection (section 15) and an explicit-relationship map (section
   18), neither of which exists anywhere in the source documents, plus
   priority.scoring_formula, which diagnostic.json marks TBD. Stubbed.

2. ORDERING already-identified priorities against each other. Section
   17 gives this as a concrete, fully-specified precedence rule (a
   tiered comparison, not a numeric formula) -- implemented for real
   below as order_priorities(), and independently testable with
   synthetic signal inputs even while (1) is stubbed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import UndefinedDiagnosticRuleError
from .types import Finding, Priority

_SEVERITY_TIER = {
    "critical": 1,
    "high_broad": 2,
    "high": 3,
    "moderate_concentrated": 4,
    "moderate": 5,
    "low": 6,
}


@dataclass(frozen=True)
class PrioritySignals:
    """
    The inputs order_priorities() needs for one candidate priority,
    per Design Spec section 16's four signals (severity, concentration,
    explicit relationships, potential impact) and section 17's
    tie-breakers. How these signals get computed from real findings is
    exactly the undefined part of (1) above -- this type lets the
    ordering RULE be tested on its own with hand-supplied values.
    """

    priority: Priority
    severity: str  # "critical" | "high" | "moderate" | "low"
    broad_or_concentrated_impact: bool  # only meaningful when severity == "high"
    meaningful_concentration: bool  # only meaningful when severity == "moderate"
    explicit_relationship_breadth: int  # tie-break 1: higher = broader
    concentration: int  # tie-break 2: higher = more concentrated
    journey_relevance: int  # tie-break 3: higher = more relevant


def _tier(signals: PrioritySignals) -> int:
    sev = signals.severity
    if sev == "critical":
        return _SEVERITY_TIER["critical"]
    if sev == "high":
        return (
            _SEVERITY_TIER["high_broad"]
            if signals.broad_or_concentrated_impact
            else _SEVERITY_TIER["high"]
        )
    if sev == "moderate":
        return (
            _SEVERITY_TIER["moderate_concentrated"]
            if signals.meaningful_concentration
            else _SEVERITY_TIER["moderate"]
        )
    if sev == "low":
        return _SEVERITY_TIER["low"]
    raise ValueError(f"unrecognized severity {sev!r}")


def order_priorities(candidates: list[PrioritySignals]) -> list[Priority]:
    """
    Design Spec section 17's precedence order, applied as a stable sort:

      1. Critical severity
      2. High severity with broad/concentrated impact
      3. High severity
      4. Moderate severity with meaningful concentration
      5. Moderate severity
      6. Low severity

    Within equivalent severity: broader explicit relationship, then
    greater concentration, then greater journey relevance.
    """
    ordered = sorted(
        candidates,
        key=lambda s: (
            _tier(s),
            -s.explicit_relationship_breadth,
            -s.concentration,
            -s.journey_relevance,
        ),
    )
    return [s.priority for s in ordered]


def generate_priorities(definition: dict, findings: list[Finding]) -> list[Priority]:
    rule = definition.get("priority", {}).get("scoring_formula")
    if rule == "TBD":
        return []
    raise UndefinedDiagnosticRuleError(
        "priority.scoring_formula is no longer 'TBD' but generate_priorities() "
        "has no interpreter for it yet, and no pattern/relationship map exists "
        "to group findings into priorities in the first place. Update this "
        "function before relying on this definition's priorities."
    )
