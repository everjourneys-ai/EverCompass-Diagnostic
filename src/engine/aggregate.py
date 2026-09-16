"""
Dimension and Journey Stage aggregation (Design Spec v1.0 sections 13-14).

Both sections are explicit that this is "not a simple average" and
that "the exact aggregation classification is proprietary diagnostic
logic" -- i.e. whatever single label or score a dimension/journey
"is at" overall is undefined (aggregation.dimension.method /
aggregation.journey.method are TBD in diagnostic.json; see
DECISIONS.md).

What both sections *do* specify is what the aggregate preserves:
criterion results, findings, and a classification distribution. That
part is purely mechanical -- group by dimension or journey_stage, tally
-- and is fully implemented here. No reduced classification is
computed or invented.
"""

from __future__ import annotations

from .types import AggregateResult, CriterionResult, Finding


def _aggregate(
    group_ids: list[str],
    group_attr: str,
    criterion_results: list[CriterionResult],
    findings: list[Finding],
) -> dict[str, AggregateResult]:
    result: dict[str, AggregateResult] = {}
    for group_id in group_ids:
        group_criteria = [
            cr for cr in criterion_results if getattr(cr, group_attr) == group_id
        ]
        group_findings = [
            f for f in findings if getattr(f, group_attr) == group_id
        ]

        distribution: dict[str, int] = {}
        for cr in group_criteria:
            if cr.classification is not None:
                distribution[cr.classification] = distribution.get(cr.classification, 0) + 1

        result[group_id] = AggregateResult(
            criteria=[cr.criterion_id for cr in group_criteria],
            findings=[f.finding_id for f in group_findings],
            classification_distribution=distribution,
        )
    return result


def aggregate_dimensions(
    definition: dict,
    criterion_results: list[CriterionResult],
    findings: list[Finding],
) -> dict[str, AggregateResult]:
    dimension_ids = [d["id"] for d in definition["dimensions"]]
    return _aggregate(dimension_ids, "dimension", criterion_results, findings)


def aggregate_journey_stages(
    definition: dict,
    criterion_results: list[CriterionResult],
    findings: list[Finding],
) -> dict[str, AggregateResult]:
    journey_stage_ids = [j["id"] for j in definition["journey_stages"]]
    return _aggregate(journey_stage_ids, "journey_stage", criterion_results, findings)
