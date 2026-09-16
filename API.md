# EverCompass Diagnostic API

A thin FastAPI layer around the deterministic Assessment Engine (`src/engine/`), via an
application layer (`src/application/`) that resolves diagnostic definitions and orchestrates
assessment. See `ENGINE_STATUS.md` and `DECISIONS.md` for the underlying methodology; this
document only covers the HTTP layer.

```
HTTP Request -> FastAPI (src/api) -> Application Layer (src/application) -> Assessment Engine
(src/engine) -> Diagnostic Definition (src/definitions/diagnostic.json) -> Structured Result
-> HTTP Response
```

FastAPI contains no assessment/scoring methodology -- every route delegates to the application
layer. The engine has no knowledge of HTTP, FastAPI, or any of this.

## Running locally

Install the runtime dependencies (stdlib-only `src/engine` needs none of this; only the API layer does):

```bash
pip install -r requirements.txt
```

Start the API with auto-reload:

```bash
PYTHONPATH=src uvicorn api.main:app --reload
```

The API is then at `http://127.0.0.1:8000`. Interactive OpenAPI docs (Swagger UI) are at
`http://127.0.0.1:8000/docs`; the raw OpenAPI schema is at `/openapi.json`.

## Endpoints

### `GET /health`

Liveness only. Phase 1 has no database or external dependency to check readiness against (see
`src/api/routes/health.py`), so this deliberately does not pretend to.

```json
{ "status": "ok" }
```

### `GET /api/v1/diagnostics`

Discovery metadata for every published diagnostic. No proprietary content.

```json
[
  { "diagnostic_id": "evercompass", "name": "EverCompass Diagnostic", "version": "1.0.0", "status": "published" }
]
```

### `GET /api/v1/diagnostics/{id}`

Everything a frontend needs to render the diagnostic and collect a valid response set: journey
stages, dimensions, all 51 criteria (id, journey_stage, dimension, question, response_type), the
1-5 response scale's option labels, and the applicability rule. See "Public vs internal data" below
for what this deliberately excludes.

```json
{
  "diagnostic_id": "evercompass",
  "name": "EverCompass Diagnostic",
  "version": "1.0.0",
  "status": "published",
  "journey_stages": [{ "id": "attract", "label": "Attract", "description": "..." }, "... 3 more"],
  "dimensions": [{ "id": "marketing_strategy", "label": "Marketing Strategy", "description": "..." }, "... 3 more"],
  "response_scale": [
    { "score": 1, "classification": "needs_attention", "meaning": "Absent / severely limited" },
    "... 4 more"
  ],
  "applicability": { "values": ["applicable", "not_applicable"], "note": "Non-applicable capabilities are not weaknesses." },
  "criteria": [
    {
      "id": "attract.marketing_strategy.audience",
      "journey_stage": "attract",
      "dimension": "marketing_strategy",
      "question": "How clearly defined is the audience your business is trying to attract?",
      "response_type": "maturity_1_5"
    },
    "... 50 more"
  ]
}
```

`404 unknown_diagnostic` if `{id}` isn't a known, published diagnostic.

### `POST /api/v1/diagnostics/{id}/assess`

Submit a completed response set and get the Structured Result back.

Request body:

```json
{
  "diagnostic_version": "1.0.0",
  "responses": [
    { "criterion_id": "attract.marketing_strategy.audience", "value": 3, "evidence": "...", "applicability": "applicable" },
    "... one entry per criterion, all 51 required"
  ]
}
```

`diagnostic_version` is required and must match exactly -- the API never silently substitutes a
different published version (see "Versioning" below).

Response body: the engine's Structured Result, exactly as shaped by `schema/result.schema.json`
(`assessment_id`, `diagnostic_id`, `diagnostic_version`, `engine_version`, `criterion_results`,
`findings`, `dimensions`, `journey_stages`, `priorities`, `system_summary`). No `overall_score`
field exists anywhere in this response, by design (ADR-009 in `DECISIONS.md`).

## Error format

Every error response, from every layer (request parsing, response validation, unknown
diagnostic/version), uses the same shape:

```json
{ "error": { "code": "invalid_value", "message": "1 response(s) have an invalid value (must be an integer 1-5 when applicable)", "details": ["attract.marketing_strategy.audience"] } }
```

`details`, when present, is a list of the offending `criterion_id`s -- never a Python traceback or
internal implementation detail.

| HTTP status | `code` | When |
|---|---|---|
| 400 | `malformed_request` | Request body doesn't match the expected shape (missing/extra/wrong-type fields) |
| 400 | `missing_response` | A criterion in the diagnostic has no response |
| 400 | `unknown_criterion` | A response references a criterion_id not in the diagnostic |
| 400 | `invalid_value` | A response value is out of range (not an integer 1-5 when applicable) |
| 400 | `duplicate_response` | The same criterion_id was submitted more than once |
| 400 | `contradictory_applicability` | `applicability: "not_applicable"` with a non-null `value` |
| 404 | `unknown_diagnostic` | `{id}` is not a known, published diagnostic |
| 404 | `unknown_diagnostic_version` | `{id}` is known, but not published at the requested `diagnostic_version` |
| 500 | `internal_error` | Unexpected server-side failure; logged server-side, no detail exposed |

## Versioning

- `diagnostic_version` in the request must exactly match a published version of `{id}`; there is
  no implicit "latest" substitution on assess (list/detail endpoints do default to the latest
  published version when no version is specified, since those are read-only discovery/content
  endpoints, not an assessment against a specific pinned version).
- The engine's own `engine_version` (independent of `diagnostic_version`, see `src/engine/engine.py`)
  is always present in the result.
- Published diagnostic definitions are immutable (Design Spec section 24) and this API never
  mutates one -- the repository only reads `src/definitions/*.json` at startup.

## CORS

Configurable via the `EVERCOMPASS_CORS_ORIGINS` environment variable (comma-separated origins).
Defaults to common local dev origins only (`http://localhost:3000`, `http://localhost:5173`, and
their `127.0.0.1` equivalents) -- no production/Framer domain is hardcoded, since none is defined
anywhere else in this repository. Set the real origin(s) via the environment variable once known:

```bash
EVERCOMPASS_CORS_ORIGINS="https://your-framer-site.com,http://localhost:3000" uvicorn api.main:app --reload
```

## Security / API hygiene (Phase 1)

- No authentication (not required by the architecture for this phase).
- No persistence -- assessment results are computed and returned, never stored.
- No Supabase, no HubSpot, no AI.
- Request/response bodies (including `evidence` text and submitted response values) are never
  logged -- `src/api/middleware.py`'s access log records only method, path, status code, and
  duration.
- No Python traceback or internal exception detail is ever returned in an HTTP response body;
  unexpected errors are logged server-side and returned as a generic `internal_error`.

## Public vs internal diagnostic data

`GET /api/v1/diagnostics/{id}` exposes only what a frontend needs to render questions and collect
responses. It never exposes: `severity_model`, `finding_model.generation_rule`,
`aggregation.*.method.condition_rules`, `priority.scoring_formula`, `criteria[*].impact`,
`criteria[*].journey_relevance`, or `rule_types`. See `src/application/public_view.py` for the
exact projection and why. The Assessment Engine still receives the *complete* internal
definition internally (`src/application/repository.py`) -- only the HTTP response to
`GET /api/v1/diagnostics/{id}` is filtered.

## Running the tests

```bash
pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
```

This runs the engine's unit/golden/invariant tests and the API tests (`tests/test_api_*.py`)
together. The API tests use the real deterministic engine end to end (no mocking) via FastAPI's
`TestClient` (`tests/api_helpers.py`); only `httpx` (a `TestClient` dependency) is needed beyond
`requirements.txt`.
