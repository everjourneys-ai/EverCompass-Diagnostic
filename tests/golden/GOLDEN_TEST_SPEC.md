# EverCompass Golden Test Specification

Per Architecture v1.2 §29 / Design Spec v1.0 §29: a golden test is

```
Diagnostic Version + Input Responses = Expected Result
```

fixed as a permanent regression fixture. This document defines the format, the required coverage, and — honestly, per this project's practice throughout — exactly which categories are fully specifiable today versus blocked on work that hasn't happened yet.

## Status

`src/definitions/diagnostic.json` is **frozen as EverCompass Diagnostic Definition v1.0** (`status: published`). Every methodology field is resolved — see `DECISIONS.md` and the definition's own `*_model`/`aggregation`/`priority` sections. **The assessment engine (`src/engine/`) is fully implemented** against v1.0: `validate_responses()`, `evaluate_criterion()`/`evaluate_all_criteria()`, `generate_findings()`, severity derivation, dimension/journey aggregation (including dominant-condition classification), concentration, and `generate_priorities()` are all real, non-stub implementations (see `ENGINE_STATUS.md`). This means:

- Validation-tier fixtures (`expect == "error"`) pass against `engine.evaluate()`, which raises the expected typed error.
- Full-assessment-tier fixtures (`expect == "result"`) get a real, field-by-field comparison against `engine.evaluate()`'s actual output — `tests/test_golden.py::FullAssessmentTierGoldenTests::test_full_assessment_fixtures_against_the_current_engine` — and all currently pass.

The test runner (`tests/test_golden.py`) asserts this directly, per fixture, rather than hiding it.

## Fixture format

Each file under `tests/golden/fixtures/*.json`:

```json
{
  "name": "...",
  "category": "response | rule | aggregation | priority | version",
  "description": "...",
  "diagnostic_version": "1.0.0",
  "responses": [ {"criterion_id": "...", "value": ..., "evidence": "...", "applicability": "..."} ],
  "expect": "error" | "result",
  "expected_error": "MissingResponseError" ,     // when expect == "error"
  "expected_result": { ...AssessmentResult shape... }  // when expect == "result"
}
```

`expected_result`, when present, is a full `AssessmentResult` matching `schema/result.schema.json`.

## How `expected_result` values were derived

**Originally, not by hand-arithmetic and not by extending the engine.** When these fixtures were first authored, `src/engine` had no implementation yet for findings, severity, or dimension/journey dominant conditions, so a throwaway, uncommitted oracle script (not part of this repository) contained a temporary interpreter for the then-already-frozen declarative rules (`finding_model.generation_rule`, `severity_model.derivation_rule`, `aggregation.*.method.condition_rules`), used only to compute fixture expectations by mechanical application of those rules — not by guessing. Validation and per-criterion scoring were computed by calling the real, already-existing `src/engine/validate.py`/`evaluate.py` directly.

**Since then**, the real engine implementation superseded that temporary interpreter, and every full-assessment fixture's `expected_result` was regenerated from and is now continuously checked against the real, committed `src/engine` (including two later rounds of methodology-decision updates to `aggregation.*.method.condition_rules`, each of which required regenerating the `dimensions`/`journey_stages` fields of the fixtures it affected). `tests/test_golden.py` runs this comparison on every test run — there is no separate oracle to keep in sync going forward.

## Required coverage (Architecture §29) and how each is covered

| Category | Required cases | Fixture(s) | Status |
|---|---|---|---|
| **Response** | valid 1 | `full_all_needs_attention` | Passes |
| | valid 5 | `full_all_operationalized` | Passes |
| | invalid 0 | `invalid_value_zero` | Passes |
| | invalid 6 | `invalid_value_six` | Passes |
| | missing response | `missing_response` | Passes |
| | duplicate response | `duplicate_response` | Passes |
| | not applicable | `full_not_applicable` | Passes |
| **Rule** | threshold | exercised by every full-assessment fixture (the only rule type any v1.0 criterion uses) | Passes |
| | match / conditional / weighted_sum / cross_reference | **out of scope for v1.0 golden fixtures** — no v1.0 criterion uses them; correct rejection (`UnsupportedRuleTypeError` / deferred) is already covered by `tests/test_evaluate.py` unit tests, not duplicated here | N/A |
| **Aggregation** | one finding | `full_single_weak_criterion` | Passes |
| | multiple findings | `full_concentrated_marketing_strategy` | Passes |
| | concentrated findings | `full_concentrated_marketing_strategy` | Passes |
| | mixed classifications | `full_concentrated_marketing_strategy` | Passes |
| | cross-journey findings | `full_concentrated_marketing_strategy` (spans attract/engage/convert) | Passes |
| **Priority** | critical finding | `full_critical_finding` | Passes |
| | multiple high findings | `full_multiple_high_findings` | Passes |
| | competing priority candidates | **not specifiable yet — see Known gap** | Not written |
| | no priority-worthy findings | `full_all_operationalized` (zero issue findings) | Passes |
| **Version** | same responses -> same result every time | `tests/test_engine.py::test_determinism_same_inputs_same_output`, plus `tests/test_invariants.py` | Passes |
| | wrong version rejected | `wrong_diagnostic_version` | Passes |

Additional fixtures beyond the minimum:
- `duplicate_response`, `contradictory_not_applicable`, `unknown_criterion` — the remaining Design Spec §24 validation categories not explicitly named in §29's list but required by it.

## Known gap: "competing priority candidates" is not specifiable yet

Per the last two validation rounds' finding J: **what makes a set of findings "related" in the first place** (Design Spec §15, Pattern) is not defined by any source document or decision made in this project so far. `priority.scoring_formula.concentration_determination_rule` defines the *thresholds* (isolated=1, repeated=2, concentrated=3-4, systemic=5+/spans≥2 journeys) but operates on a related-findings set that nothing yet defines how to construct. A "competing priority candidates" scenario specifically requires grouping multiple findings into two or more distinct priorities and ranking them against each other — which requires that grouping step. Writing an expected result for this case would mean inventing the grouping logic, which this project has consistently avoided doing. **This fixture is deliberately not written.** It should be added once that dependency is resolved.

## What "passing" means

Running `tests/test_golden.py` shows both tiers green: validation-tier fixtures raise the specific typed error each names (`expected_error`), and full-assessment-tier fixtures match the real engine's output field-by-field (`criterion_results`, `findings`, `dimensions`, `journey_stages`, `priorities`, `system_summary`). A mismatch on either tier is a real regression to investigate — there is no longer an expected/tolerated failure mode on this suite.
