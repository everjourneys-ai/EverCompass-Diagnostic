"""
Request contract for POST /api/v1/diagnostics/{id}/assess.

Deliberately loose on `value`/`applicability`: this model only enforces
JSON *shape* (types, required fields) -- FastAPI/Pydantic's job per the
architecture (see src/api/__init__.py). Range/enum/business-rule checks
(value must be 1-5, applicability must be a known value, criterion_id
must be a real criterion, no duplicates, no contradictory not_applicable
state) stay exclusively in engine.validate.validate_responses(), which
the application layer calls unmodified. Duplicating any of that here
would mean the same bad input could get flagged 400 malformed_request by
FastAPI in one code path and 400 invalid_value by the engine in another,
depending on which layer happened to notice first -- one source of truth
is worth the extra ambiguity than none.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ResponseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_id: str
    value: Optional[int] = None
    evidence: str
    applicability: str


class AssessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnostic_version: str
    responses: list[ResponseIn]
