"""
System summary (Design Spec v1.0 section 21). Purely descriptive
tallies over already-computed criterion_results / findings /
priorities -- no new scoring decisions, with one exception flagged
below.
"""

from __future__ import annotations

from .types import CriterionResult, Finding, Priority, SystemSummary

_SEVERITY_KEYS = ("critical", "high", "moderate", "low")


def build_system_summary(
    definition: dict,
    criterion_results: list[CriterionResult],
    findings: list[Finding],
    priorities: list[Priority],
) -> SystemSummary:
    criteria_total = len(criterion_results)
    criteria_applicable = sum(1 for cr in criterion_results if cr.score is not None)
    criteria_not_applicable = criteria_total - criteria_applicable

    severity_counts = {key: 0 for key in _SEVERITY_KEYS}
    for f in findings:
        if f.severity in severity_counts:
            severity_counts[f.severity] += 1

    # ASSUMPTION, not specified by either source document: a journey
    # stage / dimension "requires attention" if it has at least one
    # `issue`-type finding, of any severity. Neither document defines
    # this cutoff (e.g. whether a single `low` issue should count).
    # Inert today since generate_findings() is stubbed to [] -- flagged
    # here rather than silently baked in, for whoever defines
    # finding_model.generation_rule to confirm or override.
    journey_order = [j["id"] for j in definition["journey_stages"]]
    dimension_order = [d["id"] for d in definition["dimensions"]]
    journeys_with_issues = {f.journey_stage for f in findings if f.type == "issue"}
    dimensions_with_issues = {f.dimension for f in findings if f.type == "issue"}

    return SystemSummary(
        criteria_total=criteria_total,
        criteria_applicable=criteria_applicable,
        criteria_not_applicable=criteria_not_applicable,
        findings_total=len(findings),
        severity=severity_counts,
        priority_count=len(priorities),
        journeys_requiring_attention=[j for j in journey_order if j in journeys_with_issues],
        dimensions_requiring_attention=[d for d in dimension_order if d in dimensions_with_issues],
    )
