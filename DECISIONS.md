# EverCompass Diagnostic Engine — Decisions Log (v1.2 → v1.2.1)

**Status:** ADR-009 through ADR-015 below were made by Claude per explicit instruction to resolve the two source documents' contradictions, in order to build the JSON Schema and `diagnostic.json`. They are not formally ratified the way `Architecture v1.2`'s ADR-001–008 were — they should be reviewed by Ivan and either adopted into a formal v1.3 Architecture revision or overridden. Separately from this ADR log, every remaining open methodology question these ADRs left as "still undefined" below (finding-generation trigger, severity derivation, aggregation logic, priority formula, criterion impact/journey_relevance) has since been resolved as explicit, later decisions and is now encoded declaratively in `src/definitions/diagnostic.json` (`status: "published"`, v1.0.0) — see that file's own `*_model`/`aggregation`/`priority` sections and this repo's commit history for how. The "Still undefined" list at the bottom of this file is kept as the historical record of what was genuinely open at ADR-009–015's time of writing, not as a statement of current status.

**Sources reconciled:**
- `Evercompass-diagnostic-engine-architecture-v1_2` (Notion)
- `EverCompass Diagnostic Engine Design Specification v1.0` (Notion)

Continuing the ADR numbering from Architecture v1.2 §20 (which ends at ADR-008).

---

## ADR-009 — No overall EverCompass score

**Context:** Architecture v1.2's engine pseudocode (§9) and AI-input example (§13) compute and carry a single `overall_score` and a single `classification` (e.g. `"Established"`). Design Specification v1.0 §20 explicitly rejects this by design: *"V1 deliberately does not reduce the entire business to a single number... The system is designed to reveal structure, patterns, and areas of attention rather than allow an average score to hide important conditions."*

**Decision:** Follow the Design Specification. There is no `overall_score` and no single top-level classification anywhere in the Assessment Result. The primary model is **Journey + Lens + Findings + Priorities** (Spec §20).

**Reason:** The Spec's rejection of an overall score is a stated, reasoned design principle, not an incidental omission. Architecture's `overall_score` appears only in illustrative pseudocode/examples with no ADR of its own backing it. Where the two documents disagree on the diagnostic model's actual shape, the Specification governs — it is the document Architecture §21 itself defines as the one that decides "what the system evaluates."

**Consequences:** Architecture §9's evaluation-order pseudocode and §13's AI-input JSON example are both superseded on this point. `classify()` operates per-criterion only (score → classification via the Maturity Model). Dimension/Journey-level "classification" is a distribution summary (counts per classification band), not a single reduced label.

---

## ADR-010 — Criterion evaluation is a graded 1–5 maturity score, not pass/fail

**Context:** Architecture's `evaluate_criterion` returns `{passed: bool, raw_score}`, and `findings = [criterion results where passed == False]`. The Spec has no pass/fail concept: every applicable criterion gets a 1–5 score and a classification (§6), and findings are typed `issue | opportunity | strength` (§10) — not every criterion produces one, and a *good* result can also produce a finding (a `strength`).

**Decision:** Follow the Design Specification. Criterion evaluation produces a score (1–5, or `null` if `not_applicable`) and a classification from the Maturity Model table — not a boolean. Finding generation (which score/pattern triggers which finding type) is a separate, later step, and remains undefined (see "Still Undefined" below) — it is not simply "criterion failed."

**Reason:** The Spec is the more specific, more recently authored, "Design Complete" description of this exact mechanic. Architecture's pass/fail framing reads as its generic illustration of "how a threshold rule works in the abstract," not a decision that *this* criterion's evaluation must collapse to boolean.

**Consequences:** `engine/evaluate.py` (not built in this pass) must evaluate against the Maturity Model bands, not a single cutoff. Finding-generation logic remains an open gap.

---

## ADR-011 — No per-criterion `weight` field in V1

**Context:** Architecture's domain model requires every `Criterion` to carry a `weight`, used in `weighted_sum` aggregation to compute category/dimension/overall scores. The Spec's canonical criterion schema (§23) has no `weight` field, and explicitly defers `weighted_sum` to "future composite rules... deliberately defined" — consistent with ADR-009 removing the need for any single reduced score.

**Decision:** V1 criteria carry no `weight` field. Dimension/Journey aggregation (not built in this pass) uses the classification-distribution approach the Spec describes (§13: "not a simple average"), not a weighted average.

**Reason:** A per-criterion weight only matters if something reduces multiple criteria to one number. ADR-009 already removes that requirement at the dimension/journey/overall level.

**Consequences:** `weighted_sum` remains a supported rule *type* in the schema (for future use, e.g. a future composite criterion) but is not exercised by any V1 criterion or by dimension/journey aggregation.

---

## ADR-012 — Priority generation is in-scope for the deterministic engine, distinct from root-cause inference

**Context:** Architecture never mentions Priorities or Patterns in its engine pseudocode, repo layout, or API contract. The Spec lists Priority generation as included in V1 (§30) with a defined precedence order (§17), while also keeping causal/root-cause status deliberately shallow and Phase-3-deferred (§18) — consistent with Architecture's own ADR-008.

**Decision:** Priority generation (severity + concentration + explicit relationships + impact → an ordered priority list, per Spec §16–17) is part of the deterministic V1 engine, alongside `evaluate.py` / `score.py` / `classify.py`. It does not perform causal inference — it only orders already-computed findings. Root-cause status stays limited to the three shallow labels in Spec §18 (`none_identified / explicit_relationship / potential_relationship`).

**Reason:** This reconciles Architecture's ADR-008 with the Spec's explicit V1 inclusion of Priority: the two are compatible once "priority ordering" and "root-cause inference" are recognized as distinct operations, which the Spec's own §15–18 structure already implies.

**Consequences:** Architecture's recommended repo structure (§6) needs one more engine module for this (not built in this pass). Architecture §13's `priority_gaps` field in the AI-input example is understood to be populated by the deterministic engine, not computed ad hoc by the AI layer.

---

## ADR-013 — Canonical dimension name: "Brand Identity" (not "Brand Voice")

**Context:** Architecture v1.2 and this repository's existing `/evercompass` marketing page (`src/data/evercompass.ts`, `src/components/evercompass/FourCapabilities.astro`) both use "Brand Voice." The Design Specification uses "Brand Identity" throughout its full 51-criterion catalog.

**Decision:** The canonical dimension id is `brand_identity`, label "Brand Identity."

**Reason:** The Spec is the more detailed, more recently authored source for the diagnostic model specifically — all 51 criteria are written against "Brand Identity." Reconciling a handful of Architecture-doc references and the marketing page's copy is lower-cost than renaming a live 51-criterion catalog.

**Consequences:** `diagnostic.json` uses `brand_identity` everywhere. This decision does **not** change the marketing page's existing "Brand Voice" copy — that's a separate, non-blocking content edit, out of scope here unless requested.

---

## ADR-014 — Canonical field name: `journey_stage` (not `Category`)

**Context:** Architecture wraps journey stage in an abstraction it calls `Category` (`category_id` FK, "Category and Dimension are two independent axes"). The Spec's canonical criterion schema uses `journey_stage` directly, with no separate `Category` indirection layer.

**Decision:** The schema and `diagnostic.json` use `journey_stage` as the field name. Where Architecture's prose says "Category," read it as `journey_stage`.

**Reason:** Same concept; the Spec's field name is what needs to be machine-readable in the definition file being built. Introducing a synonymous wrapper term adds a name to reconcile without adding meaning.

**Consequences:** Vocabulary alignment only — no change to the actual data model (Architecture ADR-003/004 already describe `journey_stage`/`dimension` as two independent axes; this only renames one of them).

---

## ADR-015 — Frontend / repo location

**Context:** Both documents assume a Framer frontend calling a separate Python/FastAPI service repo. The diagnostic content and engine were first drafted inside `EverJourneys` (an Astro/TypeScript marketing site with no Python service and an existing **static, non-diagnostic** `/evercompass` explainer page), at repo root, outside `src/`, specifically so they could be lifted into a separate service repo later without restructuring.

**Decision:** Resolved by migration, not by further ADR text: the diagnostic definition, schema, and Assessment Engine now live in their own dedicated repository (`everjourneys-ai/EverCompass-Diagnostic`), separate from the `EverJourneys` Astro site. `src/definitions/diagnostic.json` and `src/engine/` are this repo's canonical content and code — there is no longer a parallel copy at this repo's root (an earlier, pre-migration duplicate of both the definition and its schema existed briefly at `definitions/evercompass/v1/` and `schema/diagnostic.schema.json`; it predated every methodology decision below and has been removed as stale, superseded content).

**Reason:** Once the Assessment Engine needed to exist as real, runnable Python, keeping it inside an Astro/TypeScript site stopped making sense; a dedicated repo is the natural home for the FastAPI layer this content is meant to be wrapped by next.

**Consequences:** Frontend/hosting for the eventual FastAPI + Framer stack is still not decided — that remains a genuinely open question, just no longer entangled with "which repo does the diagnostic content live in."

---

## Still undefined at ADR-009–015's time of writing — historical record

Per the original instruction not to invent diagnostic rules, weights, thresholds, severity mappings, recommendations, or proprietary decision logic, the following were explicit, labeled gaps in the artifacts produced by this ADR log's original pass (structurally stubbed as `null`, empty, or omitted — never filled with a guessed value). **Status as of `diagnostic.json` v1.0.0 (`published`) is annotated per item** — most have since been resolved by later, explicit decisions; two remain genuinely open and still deliberately not invented:

- **Per-criterion severity rule** (`severity.rule`) — Spec §11 explicitly forbids deriving severity as a simple function of score; no alternative rule was given at the time. **Resolved:** `severity_model.derivation_rule` is a `classification_impact_matrix` (classification × `criteria[*].impact`), assigned for all 51 criteria.
- **Dimension/Journey/Priority aggregation logic** (`aggregation.dimension`, `.journey`, `.priority`) — Spec §13 calls this "proprietary diagnostic logic," explicitly undefined at the time. **Resolved:** `aggregation.dimension.method`/`aggregation.journey.method` are six-tier `condition_rules` (critical, high, moderate, developing, operationalized, strong); `priority.scoring_formula` is a `weighted_product`.
- **Finding-generation trigger logic** — what score/condition/pattern actually creates a finding, and of which type (`issue`/`opportunity`/`strength`). **Resolved:** `finding_model.generation_rule` is a `classification_mapping` (needs_attention/developing → issue, strong/operationalized → strength; `opportunity` is schema-supported but never produced by this mapping — see the mapping's own `opportunity_note`).
- **Priority precedence formula** — Spec §17 gives an ordered list of qualitative signals, not a scoring function or cutoffs. **Resolved for the ordering `generate_priorities()` actually uses:** `priority_score = severity_weight × impact_weight × concentration_weight × journey_relevance_weight`, read from `priority.scoring_formula`. (Spec §17's original qualitative precedence rule is also fully implemented, as `order_priorities()` — see `ENGINE_STATUS.md`'s "Known internal inconsistency" note for why two orderings coexist.)
- **Relationship/pattern map** — which criterion groupings form a "pattern" (Spec §15 gives two illustrative examples, not an exhaustive map) or count as an `explicit_relationship` for root-cause status (§18). **Still open, deliberately deferred, not invented:** `src/engine/concentration.py` fixes concentration at `"isolated"` for every finding in v1.0 rather than guess at a grouping rule neither source document specifies.
- **Recommendation copy** (`recommendations.json`) — does not exist in either document. **Still open** — out of scope for the deterministic engine.
- **`finding_ref` naming convention** — Spec §23's one worked example uses `"audience_definition"` for the `audience` criterion (a `_definition` suffix), not just `"audience"`. Since only one example exists and it's a reference name rather than a scoring rule, `diagnostic.json` standardizes on the criterion's own leaf slug (e.g. `"audience"`) for all 51 criteria, for consistency. This is a naming-convention choice, not business logic, and was never revisited — flagging it here still, in case the original suffix style was intentional and should be matched instead.
