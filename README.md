# EverCompass Diagnostic — Definition, Schema & Engine

A deterministic, versioned business-diagnostic assessment system, built from:

- `Evercompass-diagnostic-engine-architecture-v1_2` (Notion)
- `EverCompass Diagnostic Engine Design Specification v1.0` (Notion)

See **`DECISIONS.md`** first — it resolves every point where the two source documents disagreed (whether there's an overall score, pass/fail vs. graded scoring, per-criterion weights, where Priority generation lives, and two naming inconsistencies), in the same ADR style as the Architecture document. Every methodology decision needed to make the definition and engine fully computable end-to-end (finding generation, severity derivation, dimension/journey aggregation, priority scoring, criterion impact assignment) has since been resolved and is recorded in the definition's own `*_model`/`aggregation`/`priority` sections, plus the session history behind this repo's commits. Concentration/pattern grouping (Design Spec §15) remains deliberately deferred, not invented — see `src/engine/concentration.py`.

## What's here

```
evercompass-diagnostic/
├── DECISIONS.md                    # ADR-009-015: how the two source documents' contradictions were resolved
├── ENGINE_STATUS.md                # current status of src/engine/
├── schema/
│   ├── diagnostic.schema.json      # validates src/definitions/diagnostic.json
│   ├── response.schema.json        # validates one respondent answer
│   ├── result.schema.json          # validates a computed Assessment Result
│   └── examples/                   # fixtures, validated against the schemas above
├── src/
│   ├── definitions/
│   │   └── diagnostic.json         # the frozen EverCompass Diagnostic Definition v1.0 (51 criteria)
│   └── engine/                     # the pure, deterministic Assessment Engine (stdlib-only Python)
└── tests/
    ├── golden/                     # Architecture §29 golden-test fixtures + spec
    └── test_*.py                   # unit tests
```

## Status

`src/definitions/diagnostic.json`'s `status` is `"published"` (v1.0.0) — per Design Spec §24, a published diagnostic definition is immutable; any further methodology change requires a new version. It contains the real 51 criteria plus every resolved methodology rule: `finding_model.generation_rule`, `severity_model.derivation_rule`, `aggregation.dimension.method` / `aggregation.journey.method` (six-tier condition_rules: critical, high, moderate, developing, operationalized, strong), and `priority.scoring_formula`. `criteria[*].impact` and `criteria[*].journey_relevance` are assigned for all 51 criteria.

`src/engine/` is fully implemented against v1.0: response validation, per-criterion scoring/classification, finding generation, severity derivation, dimension/journey aggregation (including dominant-condition classification), concentration (fixed at `"isolated"` for v1.0, per the decision above), and priority scoring/ordering. See `ENGINE_STATUS.md` for the module-by-module breakdown.

What's still deliberately not built, because no source document defines it and it was not invented here:
- Semantic related-finding grouping / pattern detection (Design Spec §15) — concentration is `"isolated"` for every finding in v1.0.
- `recommendations.json` — does not exist in either source document.
- The FastAPI layer, Supabase persistence, and AI interpretation layer (Architecture v1.2 Phases 2-3) — this repo is the deterministic engine only.

## Running the tests

Stdlib `unittest` only, no test dependency required:

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

The engine (`src/engine/`) has no HTTP, database, AI, or frontend dependency (Architecture v1.2 §3) — it is a pure function of `(diagnostic definition, responses) -> AssessmentResult`. It is intended to be wrapped by a FastAPI service and an application layer, neither of which exists in this repo yet.
