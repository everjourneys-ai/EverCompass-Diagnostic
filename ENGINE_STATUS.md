# Assessment Engine — Status

Pure Python, standard library only (`src/engine/`). Single public entrypoint:

```python
from engine import evaluate
result = evaluate(definition, responses, assessment_id="asm_001", diagnostic_version="1.0.0")
```

`definition` is a loaded `src/definitions/diagnostic.json`. `responses` is a list of `engine.types.Response`. See `tests/` for working examples.

73 tests pass (`PYTHONPATH=src:tests python3 -m unittest discover -s tests -v`), stdlib `unittest` only — no test dependency needed. A real serialized result also validates cleanly against `schema/result.schema.json` via `ajv-cli`.

## Fully implemented against Diagnostic Definition v1.0.0 (nothing invented)

Every methodology field the engine consumes (`finding_model.generation_rule`, `severity_model.derivation_rule`, `aggregation.dimension.method`/`aggregation.journey.method`, `priority.scoring_formula`, `criteria[*].impact`, `criteria[*].journey_relevance`) is resolved in the frozen, `published` definition — see `DECISIONS.md` and the definition's own `*_model`/`aggregation`/`priority` sections for how.

| Module | Does |
|---|---|
| `validate.py` | Enforces every rule in Design Spec §24: unknown diagnostic version, missing/unknown/duplicate criterion responses, invalid values, contradictory N/A state. |
| `evaluate.py` | Per-criterion score + classification via `classification_model.bands` (the Maturity Model, §6) — the only rule type any V1 criterion uses is `threshold`; any other type raises `UnsupportedRuleTypeError` rather than guessing. |
| `findings.py` — `generate_findings()` | One Finding per applicable criterion, via `finding_model.generation_rule` (a `classification_mapping`, generic interpreter). Severity via `severity_model.derivation_rule` (a `classification_impact_matrix` over classification × `criteria[*].impact`, also generic). Not_applicable criteria produce no finding. |
| `concentration.py` — `determine_concentration()` | v1.0: every finding is its own isolated group of one (`concentration = "isolated"`, `weight = 1`) — semantic related-finding grouping is deliberately deferred, not invented (see the module's own docstring). The `relationship_rules` parameter is the documented extension point for a future diagnostic version. |
| `aggregate.py` / `conditions.py` | Groups criterion results and findings by dimension/journey stage, tallies a classification distribution, and computes each group's six-tier `dominant_condition` (`critical, high, moderate, developing, operationalized, strong`, or `no_data`) via a generic `condition_rules` interpreter reading `aggregation.dimension.method`/`aggregation.journey.method`. Matches §13/§14's "not a simple average" — no single reduced numeric score is computed (ADR-009). |
| `priority.py` — `generate_priorities()` | One Priority per issue-type finding (concentration deferred, so no multi-finding grouping yet). `priority_score = severity_weight × impact_weight × concentration_weight × journey_relevance_weight`, all four weight tables read from `priority.scoring_formula`. Ordered by `priority_score` descending, ascending-`criterion_id` tie-break — this is the ordering wired into `evaluate()`. |
| `priority.py` — `order_priorities()` | A separate, independently-tested implementation of Design Spec §17's original *qualitative* precedence rule (severity tier, then relationship/concentration/journey-relevance tie-breaks). **Not called from `engine.py`** — see "Known internal inconsistency" below. |
| `summary.py` | Tallies counts (§21) from whatever criterion_results/findings/priorities it's given. |
| `engine.py` | Orchestrates the above as one pure function — no HTTP, DB, AI, clock, or randomness (Architecture v1.2 §3). `assessment_id` and `engine_version` are caller-supplied inputs, never generated internally, so identical inputs always produce an identical result (verified by `test_determinism_same_inputs_same_output` and `test_invariants.py`). The engine never mutates the `definition` dict it's given (verified by `test_invariants.py::DefinitionImmutabilityTests`). |

## Known internal inconsistency, not a bug: two priority-ordering implementations

`priority.py` contains two independently-correct, independently-tested ways to order priorities:

1. `generate_priorities()`'s numeric sort by `priority_score` (declarative, read from `priority.scoring_formula`) — this is what `evaluate()` actually uses.
2. `order_priorities()` / `PrioritySignals` — Design Spec §17's original qualitative precedence rule (broad-impact/concentration-aware severity tiers, hardcoded in `_SEVERITY_TIER`). Fully implemented and covered by `tests/test_priority_ordering.py`, but never invoked from `engine.py`'s real pipeline.

Both are internally correct and neither is a defect on its own, but only one is live. This was surfaced during the pre-API hardening pass and intentionally left as-is (no behavior change made) pending a decision on whether `order_priorities()` should be retired, or is meant to become the real ordering in a future version.

## Deliberately deferred — not invented

- **Semantic related-finding grouping / pattern detection** (Design Spec §15) — see `concentration.py`. Every finding is `"isolated"` for v1.0.
- **`recommendations.json`** — does not exist in either source document.

## What this is ready for vs. what it still needs

Running `evaluate()` today against the real `diagnostic.json` produces a fully valid, schema-conformant `AssessmentResult` for any of the 51 criteria — correct scores, classifications, findings, severities, dimension/journey dominant conditions, and priorities.

Not part of this repo, per the phased plan (Architecture v1.2 §24): the FastAPI layer, an application layer between FastAPI and this engine, Supabase persistence, and AI interpretation.
