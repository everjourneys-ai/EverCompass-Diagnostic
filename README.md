# EverCompass Diagnostic — Definition, Schema, Engine & API

A deterministic, versioned business-diagnostic assessment system, built from:

- `Evercompass-diagnostic-engine-architecture-v1_2` (Notion)
- `EverCompass Diagnostic Engine Design Specification v1.0` (Notion)

See **`DECISIONS.md`** first — it resolves every point where the two source documents disagreed (whether there's an overall score, pass/fail vs. graded scoring, per-criterion weights, where Priority generation lives, and two naming inconsistencies), in the same ADR style as the Architecture document. Every methodology decision needed to make the definition and engine fully computable end-to-end (finding generation, severity derivation, dimension/journey aggregation, priority scoring, criterion impact assignment) has since been resolved and is recorded in the definition's own `*_model`/`aggregation`/`priority` sections, plus the session history behind this repo's commits. Concentration/pattern grouping (Design Spec §15) remains deliberately deferred, not invented — see `src/engine/concentration.py`.

## What's here

```
evercompass-diagnostic/
├── DECISIONS.md                    # ADR-009-015: how the two source documents' contradictions were resolved
├── ENGINE_STATUS.md                # current status of src/engine/
├── API.md                          # how to run/use the FastAPI layer
├── requirements.txt                # API layer runtime deps (src/engine needs none)
├── requirements-dev.txt            # + test-only deps (httpx, for TestClient)
├── schema/
│   ├── diagnostic.schema.json      # validates src/definitions/diagnostic.json
│   ├── response.schema.json        # validates one respondent answer
│   ├── result.schema.json          # validates a computed Assessment Result
│   └── examples/                   # fixtures, validated against the schemas above
├── src/
│   ├── definitions/
│   │   └── diagnostic.json         # the frozen EverCompass Diagnostic Definition v1.0 (51 criteria)
│   ├── engine/                     # the pure, deterministic Assessment Engine (stdlib-only Python)
│   ├── application/                # loads/selects a diagnostic definition, orchestrates assessment,
│   │                                # builds the public (non-proprietary) diagnostic view
│   └── api/                        # FastAPI layer: routing, request/response models, CORS, error mapping
└── tests/
    ├── golden/                     # Architecture §29 golden-test fixtures + spec
    ├── test_*.py                   # engine unit/golden/invariant tests
    └── test_api_*.py               # API tests (real engine, no mocking)
```

## Status

`src/definitions/diagnostic.json`'s `status` is `"published"` (v1.0.0) — per Design Spec §24, a published diagnostic definition is immutable; any further methodology change requires a new version. It contains the real 51 criteria plus every resolved methodology rule: `finding_model.generation_rule`, `severity_model.derivation_rule`, `aggregation.dimension.method` / `aggregation.journey.method` (six-tier condition_rules: critical, high, moderate, developing, operationalized, strong), and `priority.scoring_formula`. `criteria[*].impact` and `criteria[*].journey_relevance` are assigned for all 51 criteria.

`src/engine/` is fully implemented against v1.0: response validation, per-criterion scoring/classification, finding generation, severity derivation, dimension/journey aggregation (including dominant-condition classification), concentration (fixed at `"isolated"` for v1.0, per the decision above), and priority scoring/ordering. See `ENGINE_STATUS.md` for the module-by-module breakdown.

A thin FastAPI layer (`src/api/`) and application layer (`src/application/`) now wrap the engine — see **`API.md`** for endpoints, request/response examples, error format, and how to run it locally.

What's still deliberately not built, because no source document defines it and it was not invented here:
- Semantic related-finding grouping / pattern detection (Design Spec §15) — concentration is `"isolated"` for every finding in v1.0.
- `recommendations.json` — does not exist in either source document.
- Supabase persistence and the AI interpretation layer (Architecture v1.2 Phases 2-3), and authentication — none of these are part of this Phase 1 API.

## Running the tests

Engine tests are stdlib `unittest` only, no dependency required. API tests additionally need `requirements-dev.txt` installed (`pip install -r requirements-dev.txt`) — both run together with the same command:

```bash
PYTHONPATH=src:tests python3 -m unittest discover -s tests -v
```

## Validating

Requires Node. No `package.json` dependency was added — validation is run ad hoc via `npx`:

```bash
npx ajv-cli@5 validate --spec=draft2020 -s schema/diagnostic.schema.json -d src/definitions/diagnostic.json
npx ajv-cli@5 validate --spec=draft2020 -s schema/response.schema.json -d schema/examples/response-applicable.json
npx ajv-cli@5 validate --spec=draft2020 -s schema/result.schema.json -d schema/examples/result-example.json
```

All three currently pass.

## Architectural boundary

```
HTTP Request -> FastAPI (src/api) -> Application Layer (src/application) -> Assessment Engine
(src/engine) -> Diagnostic Definition (src/definitions/diagnostic.json) -> Structured Result
```

The engine (`src/engine/`) has no HTTP, database, AI, or frontend dependency (Architecture v1.2 §3) — it is a pure function of `(diagnostic definition, responses) -> AssessmentResult`, and stays that way: `src/api/` and `src/application/` depend on `src/engine/`, never the reverse. See `API.md` for the API layer.
