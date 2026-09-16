"""
Domain types for the EverCompass Assessment Engine.

Mirrors schema/response.schema.json and schema/result.schema.json.
Plain dataclasses only -- no ORM, no HTTP framework, no third-party
dependency. The engine must stay importable and runnable with nothing
but the Python standard library (Architecture v1.2 section 3: the
engine has no HTTP, database, or AI dependency).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Response:
    """One respondent answer to one criterion (Design Spec section 5)."""

    criterion_id: str
    value: Optional[int]
    evidence: str
    applicability: str  # "applicable" | "not_applicable"


@dataclass(frozen=True)
class CriterionResult:
    """Deterministic evaluation of one response (Design Spec section 9)."""

    criterion_id: str
    journey_stage: str
    dimension: str
    score: Optional[int]
    classification: Optional[str]
    finding_id: Optional[str]


@dataclass(frozen=True)
class Finding:
    """Design Spec section 10."""

    finding_id: str
    criterion_id: str
    journey_stage: str
    dimension: str
    type: str  # "issue" | "opportunity" | "strength"
    severity: Optional[str]


@dataclass(frozen=True)
class AggregateResult:
    """
    A Dimension Result or Journey Result (Design Spec sections 13-14).

    Never a single reduced score across the whole business (ADR-009).
    dominant_condition is the per-dimension/per-journey six-tier
    condition (or "no_data") produced by aggregation.dimension.method /
    aggregation.journey.method's condition_rules -- a condition per
    dimension/journey is explicitly part of the frozen v1.0 methodology
    (Design Spec section 13's own example shows exactly this), not a
    reversal of ADR-009, which only rules out one score for the entire
    business.
    """

    criteria: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    classification_distribution: dict[str, int] = field(default_factory=dict)
    dominant_condition: str = "no_data"


@dataclass(frozen=True)
class Priority:
    """
    Design Spec section 16. One Priority per issue-type finding in v1
    (concentration is deferred -- see concentration.py -- so every
    finding is its own "isolated" group of one; there is no multi-
    finding grouping yet).

    priority_score is the internal ordering mechanism (severity_weight
    x impact_weight x concentration_weight x journey_relevance_weight)
    -- explicitly not an "EverCompass Score" or business health score
    (that would be a single number for the whole business; this is
    scoped to one specific priority).
    """

    priority_id: str
    title: str
    supporting_findings: list[str]
    journey_stages: list[str]
    dimensions: list[str]
    priority_score: int


@dataclass(frozen=True)
class SystemSummary:
    """Design Spec section 21."""

    criteria_total: int
    criteria_applicable: int
    criteria_not_applicable: int
    findings_total: int
    severity: dict[str, int]
    priority_count: int
    journeys_requiring_attention: list[str]
    dimensions_requiring_attention: list[str]


@dataclass(frozen=True)
class AssessmentResult:
    """The deterministic Structured Assessment Result (Design Spec section 19)."""

    assessment_id: str
    diagnostic_id: str
    diagnostic_version: str
    engine_version: str
    criterion_results: list[CriterionResult]
    findings: list[Finding]
    dimensions: dict[str, AggregateResult]
    journey_stages: dict[str, AggregateResult]
    priorities: list[Priority]
    system_summary: SystemSummary
