"""Public diagnostic content -- see src/application/public_view.py for
what is deliberately excluded and why."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class DiagnosticSummaryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnostic_id: str
    name: str
    version: str
    status: str


class JourneyStageOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    description: str


class DimensionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    description: str


class ResponseScaleBandOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int
    classification: str
    meaning: str


class ApplicabilityOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    values: list[str]
    note: str


class PublicCriterionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    journey_stage: str
    dimension: str
    question: str
    response_type: str


class DiagnosticPublicOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnostic_id: str
    name: str
    version: str
    status: str
    journey_stages: list[JourneyStageOut]
    dimensions: list[DimensionOut]
    response_scale: list[ResponseScaleBandOut]
    applicability: ApplicabilityOut
    criteria: list[PublicCriterionOut]
