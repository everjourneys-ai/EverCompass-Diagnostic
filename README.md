# EverCompass Diagnostic — Definition & Schema

Structured diagnostic content for the EverCompass Diagnostic Engine, built from:

- `Evercompass-diagnostic-engine-architecture-v1_2` (Notion)
- `EverCompass Diagnostic Engine Design Specification v1.0` (Notion)

See **`DECISIONS.md`** first — the two source documents disagree on several points (whether there's an overall score, pass/fail vs. graded scoring, per-criterion weights, where Priority generation lives, and two naming inconsistencies). `DECISIONS.md` resolves each one with a citable reason, in the same ADR style as the Architecture document, and lists what's still genuinely undefined and was deliberately left that way rather than invented.

## What's here

```
evercompass-diagnostic/
├── DECISIONS.md                              # ADR-009–015, resolving the two docs' contradictions
├── schema/
│   ├── diagnostic.schema.json                # validates a diagnostic definition
│   ├── response.schema.json                  # validates one respondent answer
│   ├── result.schema.json                    # validates a computed Assessment Result
│   └── examples/                             # fixtures, validated against the schemas above
└── definitions/evercompass/v1/
    └── diagnostic.json                       # the 51 real criteria, transcribed from the Spec
```

## Status

`diagnostic.json`'s `status` is `"draft"`. It contains the **real** 51 criteria (id, journey stage, dimension, question text) transcribed verbatim from the Design Specification — this is not placeholder/test-fixture content. What it does **not** contain, because neither source document defines it and it was not invented here:

- Per-criterion `severity.rule` (every criterion has it set to `null`)
- Dimension/journey/priority `aggregation` logic (all `null`)
- Finding-generation trigger logic (what makes a finding, and of which type)
- The priority-ordering formula (only qualitative signal ordering exists — Spec §17)
- The criterion relationship/pattern map (only two illustrative examples exist — Spec §15)
- `recommendations.json` (doesn't exist in either source document)

Per Architecture v1.2 §21, this is expected at this stage: schema-shaped, real-criteria content that proves the model, not yet enough to compute a defensible score. Golden tests and the `finding`/`severity`/`aggregation`/priority rules should be authored as a follow-up with Ivan, not guessed at.

## Validating

Requires Node (already a project dependency for the Astro site). No new dependency was added to `package.json` — validation was run ad hoc via `npx`:

```bash
npx ajv-cli@5 validate --spec=draft2020 -s schema/diagnostic.schema.json -d definitions/evercompass/v1/diagnostic.json
npx ajv-cli@5 validate --spec=draft2020 -s schema/response.schema.json -d schema/examples/response-applicable.json
npx ajv-cli@5 validate --spec=draft2020 -s schema/result.schema.json -d schema/examples/result-example.json
```

All three currently pass. Two negative cases were also spot-checked (an out-of-range `not_applicable` value, and an invalid `dimension` enum value) to confirm the schemas actually reject bad data rather than accepting anything.

## Not done here

Per `DECISIONS.md` ADR-015, this pass produced data only (schema + definition), not code. Still outstanding, per Architecture v1.2's Implementation Gate (§25) and phased plan (§24):

- Where this content and the eventual engine/API actually live (this repo is Astro/TypeScript with no Python service; both source documents assume a separate FastAPI service and a Framer frontend)
- The Assessment Engine itself (`evaluate` / `score` / `classify` / `priority`)
- Golden tests
- `recommendations.json`
- The FastAPI layer, Supabase persistence, and AI interpretation layer (Phases 2–3, unchanged scope from both source documents)
