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

    Deliberately has no single reduced "classification" field -- see
    DECISIONS.md ADR-009 and the diagnostic definition's
    aggregation.dimension.method / aggregation.journey.method, both
    TBD. This holds only what's mechanically computable: which
    criteria/findings belong to this group, and a tally of
    classifications actually observed.
    """

    criteria: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    classification_distribution: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Priority:
    """Design Spec section 16."""

    priority_id: str
    title: str
    supporting_findings: list[str]
    journey_stages: list[str]
    dimensions: list[str]


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
