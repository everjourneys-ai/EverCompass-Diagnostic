# Assessment Engine — Status (first draft)

Pure Python, standard library only (`src/engine/`). Single public entrypoint:

```python
from engine import evaluate
result = evaluate(definition, responses, assessment_id="asm_001", diagnostic_version="1.0.0")
```

`definition` is a loaded `src/definitions/diagnostic.json`. `responses` is a list of `engine.types.Response`. See `tests/` for working examples.

32 tests pass (`PYTHONPATH=src:tests python3 -m unittest discover -s tests -v`), stdlib `unittest` only — no test dependency needed. A real serialized result also validates cleanly against `schema/result.schema.json` via `ajv-cli`.

## Fully implemented (deterministic, nothing invented)

| Module | Does |
|---|---|
| `validate.py` | Enforces every rule in Design Spec §24: unknown diagnostic version, missing/unknown/duplicate criterion responses, invalid values, contradictory N/A state. |
| `evaluate.py` | Per-criterion score + classification via `classification_model.bands` (the Maturity Model, §6) — the only rule type any V1 criterion uses is `threshold`; any other type raises `UnsupportedRuleTypeError` rather than guessing. |
| `aggregate.py` | Groups criterion results and findings by dimension/journey stage, tallies a classification distribution. Matches §13/§14's "not a simple average" — no single reduced label is computed. |
| `priority.py` — `order_priorities()` | Implements §17's precedence rule (severity tier, then relationship/concentration/journey-relevance tie-breaks) as a real, independently-tested sort. |
| `summary.py` | Tallies counts (§21) from whatever criterion_results/findings/priorities it's given. |
| `engine.py` | Orchestrates the above as one pure function — no HTTP, DB, AI, clock, or randomness (Architecture v1.2 §3). `assessment_id` and `engine_version` are caller-supplied inputs, never generated internally, so identical inputs always produce an identical result (verified by `test_determinism_same_inputs_same_output`). |

## Deliberately stubbed — not invented

These return `[]` right now, and will raise `UndefinedDiagnosticRuleError` (loudly, not silently) if the definition's TBD marker is ever changed without a matching code update:

- **`findings.generate_findings()`** — `finding_model.generation_rule` is `TBD`. No condition exists anywhere in the source documents for when a criterion result becomes a Finding, or which type (`issue`/`opportunity`/`strength`) it becomes.
- **`priority.generate_priorities()`** — grouping findings into a Priority in the first place needs pattern/concentration detection (§15) and an explicit-relationship map (§18), neither of which exists, plus `priority.scoring_formula`, also `TBD`. (The separate *ordering* of already-identified priorities — `order_priorities()` — is fully implemented; see above.)

Because findings are always empty right now, so are `dimensions_requiring_attention` / `journeys_requiring_attention` and every severity tally — not because those code paths are wrong, but because there's nothing to feed them yet.

**One assumption flagged, not hidden:** `summary.py` treats "requiring attention" as *any journey/dimension with at least one `issue`-type finding, of any severity*. Neither source document defines this cutoff. It's inert today (no findings exist to trigger it) — confirm or override once finding generation is real.

## What this unblocks vs. what it still needs

Running `evaluate()` today against the real `diagnostic.json` produces a fully valid, schema-conformant `AssessmentResult` for any of the 51 criteria — correct scores, correct classifications, correct structural grouping — with empty findings/priorities. That's honest: it's exactly what's computable given the 5 TBDs in `DECISIONS.md`. Nothing here needs to be rewritten once those are defined — `generate_findings()` / `generate_priorities()` get real implementations, and the rest of the pipeline (`attach_finding_ids`, `aggregate_*`, `build_system_summary`, `order_priorities`) already consumes whatever they produce.

Not part of this pass, per the phased plan (Architecture v1.2 §24): FastAPI layer, Supabase persistence, AI interpretation, golden-test *fixtures* checked in as permanent regression files (current tests are real but ad hoc — formalizing them as the golden-test suite Architecture §29 describes is a reasonable next step once real finding/priority rules exist to make the interesting cases non-trivial).
