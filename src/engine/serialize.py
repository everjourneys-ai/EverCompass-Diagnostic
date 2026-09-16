"""
AssessmentResult -> plain dict/JSON, shaped to match
schema/result.schema.json exactly (so output can be validated against
it directly, e.g. in golden tests).
"""

from __future__ import annotations

from .types import AggregateResult, AssessmentResult


def _aggregate_to_dict(agg: AggregateResult) -> dict:
    return {
        "criteria": list(agg.criteria),
        "findings": list(agg.findings),
        "summary": {"classification_distribution": dict(agg.classification_distribution)},
        "dominant_condition": agg.dominant_condition,
    }


def to_dict(result: AssessmentResult) -> dict:
    return {
        "assessment_id": result.assessment_id,
        "diagnostic_id": result.diagnostic_id,
        "diagnostic_version": result.diagnostic_version,
        "engine_version": result.engine_version,
        "criterion_results": [
            {
                "criterion_id": cr.criterion_id,
                "journey_stage": cr.journey_stage,
                "dimension": cr.dimension,
                "score": cr.score,
                "classification": cr.classification,
                "finding_id": cr.finding_id,
            }
            for cr in result.criterion_results
        ],
        "findings": [
            {
                "finding_id": f.finding_id,
                "criterion_id": f.criterion_id,
                "journey_stage": f.journey_stage,
                "dimension": f.dimension,
                "type": f.type,
                "severity": f.severity,
            }
            for f in result.findings
        ],
        "dimensions": {k: _aggregate_to_dict(v) for k, v in result.dimensions.items()},
        "journey_stages": {k: _aggregate_to_dict(v) for k, v in result.journey_stages.items()},
        "priorities": [
            {
                "priority_id": p.priority_id,
                "title": p.title,
                "supporting_findings": list(p.supporting_findings),
                "journey_stages": list(p.journey_stages),
                "dimensions": list(p.dimensions),
                "priority_score": p.priority_score,
            }
            for p in result.priorities
        ],
        "system_summary": {
            "criteria_total": result.system_summary.criteria_total,
            "criteria_applicable": result.system_summary.criteria_applicable,
            "criteria_not_applicable": result.system_summary.criteria_not_applicable,
            "findings_total": result.system_summary.findings_total,
            "severity": dict(result.system_summary.severity),
            "priority_count": result.system_summary.priority_count,
            "journeys_requiring_attention": list(result.system_summary.journeys_requiring_attention),
            "dimensions_requiring_attention": list(result.system_summary.dimensions_requiring_attention),
        },
    }
