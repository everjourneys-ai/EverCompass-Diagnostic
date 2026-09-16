"""
Dimension and Journey Stage aggregation (Design Spec v1.0 sections 13-14).

Both sections are explicit that this is "not a simple average". What
they specify as preserved -- criterion results, findings, and a
classification distribution -- is purely mechanical (group and tally)
and was already implemented here. dominant_condition (the six-tier
condition, or "no_data") is now also computed, via the generic
interpreter in conditions.py reading aggregation.dimension.method /
aggregation.journey.method's condition_rules -- no reduced numeric
score is computed or invented (ADR-009).
"""

from __future__ import annotations

from .conditions import dimension_dominant_condition, journey_dominant_condition
from .types import AggregateResult, CriterionResult, Finding


def _group(criterion_results, findings, group_id, attr):
    group_cr = [cr for cr in criterion_results if getattr(cr, attr) == group_id]
    group_f = [f for f in findings if getattr(f, attr) == group_id]
    distribution: dict[str, int] = {}
    for cr in group_cr:
        if cr.classification is not None:
            distribution[cr.classification] = distribution.get(cr.classification, 0) + 1
    return group_cr, group_f, distribution


def aggregate_dimensions(
    definition: dict,
    criterion_results: list[CriterionResult],
    findings: list[Finding],
) -> dict[str, AggregateResult]:
    """Global, cross-journey view of each dimension (all criteria in
    that lens, regardless of journey stage)."""
    result: dict[str, AggregateResult] = {}
    for dimension_id in [d["id"] for d in definition["dimensions"]]:
        group_cr, group_f, distribution = _group(criterion_results, findings, dimension_id, "dimension")
        condition = dimension_dominant_condition(definition, group_cr, group_f)
        result[dimension_id] = AggregateResult(
            criteria=[cr.criterion_id for cr in group_cr],
            findings=[f.finding_id for f in group_f],
            classification_distribution=distribution,
            dominant_condition=condition,
        )
    return result


def aggregate_journey_stages(
    definition: dict,
    criterion_results: list[CriterionResult],
    findings: list[Finding],
) -> dict[str, AggregateResult]:
    dimension_ids = [d["id"] for d in definition["dimensions"]]
    result: dict[str, AggregateResult] = {}

    for journey_id in [j["id"] for j in definition["journey_stages"]]:
        journey_cr, journey_f, journey_distribution = _group(
            criterion_results, findings, journey_id, "journey_stage"
        )

        # Journey-level rules need each of the journey's 4 dimensions'
        # condition computed over ONLY this journey's slice of that
        # dimension -- a different (smaller) computation than
        # aggregate_dimensions()'s global, cross-journey view of the
        # same dimension.
        dims_in_journey: dict[str, str] = {}
        for dimension_id in dimension_ids:
            dim_cr = [cr for cr in journey_cr if cr.dimension == dimension_id]
            dim_f = [f for f in journey_f if f.dimension == dimension_id]
            dims_in_journey[dimension_id] = dimension_dominant_condition(definition, dim_cr, dim_f)

        condition = journey_dominant_condition(definition, journey_cr, journey_f, dims_in_journey)

        result[journey_id] = AggregateResult(
            criteria=[cr.criterion_id for cr in journey_cr],
            findings=[f.finding_id for f in journey_f],
            classification_distribution=journey_distribution,
            dominant_condition=condition,
        )
    return result
