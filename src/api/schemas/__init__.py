"""
Pydantic HTTP request/response contracts. These are API schemas, not
domain models -- they describe the wire format FastAPI accepts/returns
and are intentionally kept separate from engine.types' dataclasses
(domain models) and from the internal diagnostic definition dict.

src/application converts between these at the boundary (see
src/api/routes/*.py): a request body is parsed into these models, then
turned into engine.types.Response before reaching the application layer;
an engine.types.AssessmentResult is turned into a plain dict via
engine.serialize.to_dict() and returned as JSON, described here for
OpenAPI purposes by AssessmentResultOut. Keeping this indirection means
the engine's internal dataclasses can change shape without moving the
HTTP contract, and vice versa.
"""
