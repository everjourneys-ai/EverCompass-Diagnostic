"""
Public-safe projections of an internal diagnostic definition.

Architecture v1.2's proprietary/AI boundary (also Design Spec section 13:
"proprietary diagnostic logic") means a frontend rendering questions and
collecting responses must never see: severity_model, finding_model's
generation_rule, aggregation.*.method.condition_rules, priority's
scoring_formula, or criteria[*].impact / criteria[*].journey_relevance
(the two per-criterion fields that feed severity/priority weighting).
`rule_types` and evaluation.rule internals (bands_ref) are implementation
plumbing the frontend has no use for either.

What a frontend DOES need to render the diagnostic and collect valid
responses: the journey stages and dimensions (structural labels, not
proprietary), each criterion's id/journey_stage/dimension/question and
response type, the maturity response scale's option labels and
descriptions (classification_model.bands, minus nothing -- these are
literally the same classification labels that already appear in public
AssessmentResult output, e.g. criterion_results[*].classification; they
are not proprietary on their own), and the applicability rule (whether
"not applicable" is an allowed answer).

Nothing here computes anything -- it is a pure reshape of already-loaded
definition data, run once per request; no caching decision is made here.
"""

from __future__ import annotations


def build_diagnostic_summary(definition: dict) -> dict:
    """GET /api/v1/diagnostics list entry -- discovery metadata only."""
    return {
        "diagnostic_id": definition["diagnostic_id"],
        "name": definition["name"],
        "version": definition["version"],
        "status": definition["status"],
    }


def build_public_diagnostic(definition: dict) -> dict:
    """GET /api/v1/diagnostics/{id} -- everything a frontend needs to
    render the diagnostic and collect a valid response set, nothing a
    frontend doesn't (see module docstring)."""
    response_scale = [
        {"score": band["score"], "classification": band["classification"], "meaning": band["meaning"]}
        for band in definition["classification_model"]["bands"]
    ]
    applicability = {
        "values": list(definition["applicability_model"]["values"]),
        "note": definition["applicability_model"]["note"],
    }
    criteria = [
        {
            "id": c["id"],
            "journey_stage": c["journey_stage"],
            "dimension": c["dimension"],
            "question": c["question"],
            "response_type": c["response"]["type"],
        }
        for c in definition["criteria"]
    ]
    return {
        "diagnostic_id": definition["diagnostic_id"],
        "name": definition["name"],
        "version": definition["version"],
        "status": definition["status"],
        "journey_stages": [dict(j) for j in definition["journey_stages"]],
        "dimensions": [dict(d) for d in definition["dimensions"]],
        "response_scale": response_scale,
        "applicability": applicability,
        "criteria": criteria,
    }
