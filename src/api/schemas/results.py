"""
Response contract for POST /api/v1/diagnostics/{id}/assess -- mirrors
schema/result.schema.json's $defs exactly, for OpenAPI documentation.
The actual response body sent to clients is engine.serialize.to_dict()'s
output directly (already schema-conformant and covered by
tests/test_golden.py and tests/api/test_contract_e2e.py); these models
exist so FastAPI's generated docs describe the real shape, not so this
module recomputes or re-validates it.

`dimensions`/`journey_stages` are typed as dict[str, AggregateResultOut]
rather than four hardcoded named fields (marketing_strategy/ux_design/...,
attract/engage/...) on purpose: those four-and-four names are v1.0
diagnostic content, not an HTTP contract this layer should hardcode --
a future diagnostic version with different dimensions/journeys still
fits this same response shape without an API change.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class CriterionResultOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_id: str
    journey_stage: str
    dimension: str
    score: Optional[int] = None
    classification: Optional[str] = None
    finding_id: Optional[str] = None


class FindingOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    criterion_id: str
    journey_stage: str
    dimension: str
    type: str
    severity: Optional[str] = None


class AggregateSummaryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification_distribution: dict[str, int]


class AggregateResultOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria: list[str]
    findings: list[str]
    summary: AggregateSummaryOut
    dominant_condition: str


class PriorityOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    priority_id: str
    title: str
    supporting_findings: list[str]
    journey_stages: list[str]
    dimensions: list[str]
    priority_score: int


class SystemSummaryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria_total: int
    criteria_applicable: int
    criteria_not_applicable: int
    findings_total: int
    severity: dict[str, int]
    priority_count: int
    journeys_requiring_attention: list[str]
    dimensions_requiring_attention: list[str]


class AssessmentResultOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assessment_id: str
    diagnostic_id: str
    diagnostic_version: str
    engine_version: str
    criterion_results: list[CriterionResultOut]
    findings: list[FindingOut]
    dimensions: dict[str, AggregateResultOut]
    journey_stages: dict[str, AggregateResultOut]
    priorities: list[PriorityOut]
    system_summary: SystemSummaryOut
