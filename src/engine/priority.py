"""
Priority generation and ordering (Design Spec v1.0 sections 16-18).

Two genuinely different operations live here:

1. IDENTIFYING priorities -- now implemented for v1.0. Per Decision 1
   (this session), semantic relatedness grouping is deferred, so every
   issue-type finding is its own isolated Priority of one (see
   concentration.py). priority_score is the declarative weighted
   product (severity_weight x impact_weight x concentration_weight x
   journey_relevance_weight), all four weight tables read generically
   from priority.scoring_formula -- nothing hardcoded.

2. ORDERING already-identified priorities against each other. Section
   17's qualitative precedence rule is implemented as order_priorities()
   and stays untouched/independently testable. For v1.0,
   generate_priorities() orders by the numeric priority_score instead
   (descending), which is what the PRIORITY MODEL decision established
   as canonical for v1 -- with an explicit, deterministic tie-break
   (ascending criterion_id) rather than relying on input order.
"""

from __future__ import annotations

from dataclasses import dataclass

from .concentration import determine_concentration
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


def _criterion_journey_relevance(definition: dict, criterion_id: str) -> str:
    by_id = {c["id"]: c for c in definition["criteria"]}
    return by_id[criterion_id]["journey_relevance"]


def compute_priority_score(definition: dict, finding: Finding, concentration_weight: int) -> int:
    """priority_score = severity_weight x impact_weight x concentration_weight
    x journey_relevance_weight. All four tables read from
    priority.scoring_formula -- nothing hardcoded."""
    formula = definition["priority"]["scoring_formula"]
    by_id = {c["id"]: c for c in definition["criteria"]}
    impact = by_id[finding.criterion_id]["impact"]
    journey_relevance = by_id[finding.criterion_id]["journey_relevance"]

    severity_weight = formula["severity_weights"][finding.severity]
    impact_weight = formula["impact_weights"][impact]
    journey_relevance_weight = formula["journey_relevance_weights"][journey_relevance]

    return severity_weight * impact_weight * concentration_weight * journey_relevance_weight


def generate_priorities(definition: dict, findings: list[Finding]) -> list[Priority]:
    """
    One Priority per issue-type finding (Decision 1: concentration is
    deferred, so no finding is grouped with any other -- each is its
    own isolated priority candidate). Findings of type strength/
    opportunity don't "warrant attention" (Design Spec section 16) and
    are not turned into priorities.

    Ordered by priority_score descending; ties broken by ascending
    criterion_id (deterministic, based on existing result data --
    never insertion order or randomness).
    """
    rule = definition.get("priority", {}).get("scoring_formula")
    if rule == "TBD":
        raise UndefinedDiagnosticRuleError(
            "priority.scoring_formula is still 'TBD' in this definition -- "
            "cannot generate priorities."
        )

    scored: list[tuple[Priority, int, str]] = []
    n = 0
    for finding in findings:
        if finding.type != "issue":
            continue
        n += 1
        concentration = determine_concentration(finding, findings, definition)
        score = compute_priority_score(definition, finding, concentration.weight)
        priority = Priority(
            priority_id=f"P-{n:03d}",
            title=_finding_title(definition, finding),
            supporting_findings=[finding.finding_id],
            journey_stages=[finding.journey_stage],
            dimensions=[finding.dimension],
            priority_score=score,
        )
        scored.append((priority, score, finding.criterion_id))

    scored.sort(key=lambda row: (-row[1], row[2]))

    # Re-number priority_id in final (sorted) order so P-001 is always
    # the top priority -- deterministic given the stable sort above.
    ordered: list[Priority] = []
    for i, (priority, _score, _cid) in enumerate(scored, start=1):
        ordered.append(Priority(
            priority_id=f"P-{i:03d}",
            title=priority.title,
            supporting_findings=priority.supporting_findings,
            journey_stages=priority.journey_stages,
            dimensions=priority.dimensions,
            priority_score=priority.priority_score,
        ))
    return ordered


def _finding_title(definition: dict, finding: Finding) -> str:
    """finding_ref is already an approved, existing naming convention
    (diagnostic.json's criteria[*].finding.finding_ref) -- reused here
    rather than composing new recommendation-adjacent prose, which is
    not part of the frozen v1.0 methodology."""
    by_id = {c["id"]: c for c in definition["criteria"]}
    return by_id[finding.criterion_id]["finding"]["finding_ref"]
