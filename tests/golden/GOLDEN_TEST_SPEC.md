# EverCompass Golden Test Specification

Per Architecture v1.2 §29 / Design Spec v1.0 §29: a golden test is

```
Diagnostic Version + Input Responses = Expected Result
```

fixed as a permanent regression fixture. This document defines the format, the required coverage, and — honestly, per this project's practice throughout — exactly which categories are fully specifiable today versus blocked on work that hasn't happened yet.

## Status at time of writing

`src/definitions/diagnostic.json` is **frozen as EverCompass Diagnostic Definition v1.0** (`status: published`, commit `4037e1a`, local tag `diagnostic-v1.0.0`). Every methodology field is resolved — see `DECISIONS.md` and the session history. **The assessment engine (`src/engine/`) is only partially built.** `validate_responses()` and `evaluate_criterion()`/`evaluate_all_criteria()` are complete and correct against v1.0. `generate_findings()` and `generate_priorities()` are still stubs that raise `UndefinedDiagnosticRuleError` — deliberately, now that their rules are no longer `"TBD"` (see `ENGINE_STATUS.md`). This means:

- Fixtures whose expected result only requires validation or per-criterion scoring **pass today** against `engine.evaluate()`.
- Fixtures whose expected result requires findings, severity, aggregation dominant-conditions, or priorities **will currently fail** — specifically with `UndefinedDiagnosticRuleError` from `generate_findings()`, not a wrong-value assertion. That is the correct, expected failure mode right now. These fixtures are the **acceptance target** for the next phase (implementing the engine), not a currently-green suite.

The test runner (`tests/test_golden.py`) makes this explicit per-fixture rather than hiding it.

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

**Not by hand-arithmetic, and not by extending the engine.** A throwaway, uncommitted script (`/tmp/.../golden_oracle.py`, not part of this repository) was used to compute expected values mechanically:

- Validation and per-criterion scoring: by importing and calling the real, already-existing, unmodified `src/engine/validate.py` and `src/engine/evaluate.py` — this is reusing approved code, not writing new engine logic.
- Findings, severity, dimension/journey dominant conditions: `src/engine` has no implementation for these yet (see above), so the oracle script contains a **temporary, non-committed interpreter** for the now-frozen declarative rules (`finding_model.generation_rule`, `severity_model.derivation_rule`, `aggregation.*.method.condition_rules`) purely to compute fixture expectations by mechanical application of those rules — not by guessing. This interpreter is not part of the shipped engine and will be superseded by the real implementation next phase; it exists only so these 51-criterion, multi-scenario fixtures could be derived without manual arithmetic errors.
- Priority *ordering* reused the already-existing, already-tested `src/engine/priority.py::order_priorities()`.
- Priority *identification/grouping* was not computed for any fixture — see "Known gap" below.

## Required coverage (Architecture §29) and how each is covered

| Category | Required cases | Fixture(s) | Status |
|---|---|---|---|
| **Response** | valid 1 | `full_all_needs_attention` | Passes today |
| | valid 5 | `full_all_operationalized` | Passes today |
| | invalid 0 | `invalid_value_zero` | Passes today |
| | invalid 6 | `invalid_value_six` | Passes today |
| | missing response | `missing_response` | Passes today |
| | duplicate response | `duplicate_response` | Passes today |
| | not applicable | `full_not_applicable` | Blocked (findings) |
| **Rule** | threshold | exercised by every full-assessment fixture (the only rule type any v1.0 criterion uses) | Passes today (scoring layer) |
| | match / conditional / weighted_sum / cross_reference | **out of scope for v1.0 golden fixtures** — no v1.0 criterion uses them; correct rejection (`UnsupportedRuleTypeError` / deferred) is already covered by `tests/test_evaluate.py` unit tests, not duplicated here | N/A |
| **Aggregation** | one finding | `full_single_weak_criterion` | Blocked (findings) |
| | multiple findings | `full_concentrated_marketing_strategy` | Blocked (findings) |
| | concentrated findings | `full_concentrated_marketing_strategy` | Blocked (findings) |
| | mixed classifications | `full_concentrated_marketing_strategy` | Blocked (findings) |
| | cross-journey findings | `full_concentrated_marketing_strategy` (spans attract/engage/convert) | Blocked (findings) |
| **Priority** | critical finding | `full_critical_finding` | Blocked (findings/priority) |
| | multiple high findings | `full_multiple_high_findings` | Blocked (findings/priority) |
| | competing priority candidates | **not specifiable yet — see Known gap** | Not written |
| | no priority-worthy findings | `full_all_operationalized` (zero issue findings) | Blocked (findings/priority) |
| **Version** | same responses -> same result every time | `test_golden.py::test_determinism_is_reproducible` (runs a fixture twice, compares) | Passes today (validation layer); full determinism blocked same as above |
| | wrong version rejected | `wrong_diagnostic_version` | Passes today |

Additional fixtures beyond the minimum:
- `duplicate_response`, `contradictory_not_applicable`, `unknown_criterion` — the remaining Design Spec §24 validation categories not explicitly named in §29's list but required by it.

## Known gap: "competing priority candidates" is not specifiable yet

Per the last two validation rounds' finding J: **what makes a set of findings "related" in the first place** (Design Spec §15, Pattern) is not defined by any source document or decision made in this project so far. `priority.scoring_formula.concentration_determination_rule` defines the *thresholds* (isolated=1, repeated=2, concentrated=3-4, systemic=5+/spans≥2 journeys) but operates on a related-findings set that nothing yet defines how to construct. A "competing priority candidates" scenario specifically requires grouping multiple findings into two or more distinct priorities and ranking them against each other — which requires that grouping step. Writing an expected result for this case would mean inventing the grouping logic, which this project has consistently avoided doing. **This fixture is deliberately not written.** It should be added once that dependency is resolved.

## What "passing" means right now

Running `tests/test_golden.py` today should show the validation-tier fixtures green and the full-assessment-tier fixtures failing with `UndefinedDiagnosticRuleError` specifically (not any other error, and not a value mismatch). The runner asserts this explicitly. A different failure mode on a full-assessment fixture is a real bug to investigate; the `UndefinedDiagnosticRuleError` itself is not.
