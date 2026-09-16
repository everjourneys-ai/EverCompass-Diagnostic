# EverCompass Diagnostic Engine — Decisions Log (v1.2 → v1.2.1)

**Status:** Draft, made by Claude per explicit instruction to resolve documented contradictions and proceed to build the JSON Schema and `diagnostic.json`. These are not yet ratified the way `Architecture v1.2`'s ADR-001–008 were — they should be reviewed by Ivan and either adopted into a formal v1.3 Architecture revision or overridden.

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

## ADR-015 — Frontend / repo location: not resolved in this pass

**Context:** Both documents assume a Framer frontend calling a separate Python/FastAPI service repo. This repository (`EverJourneys`) is an Astro/TypeScript marketing site, with no Python service, and an existing **static, non-diagnostic** `/evercompass` explainer page.

**Decision:** Not resolved here. The JSON Schema and `diagnostic.json` built in this pass are plain data — portable to a Framer+FastAPI service, an Astro API route, or any other stack. They're placed at the repo root (`evercompass-diagnostic/`), outside `src/`, specifically so they can be lifted into a separate service repo later without restructuring, or left in place if the engine ends up living here instead.

**Reason:** This decision affects the Application/API layer and hosting, not the diagnostic content itself. Deciding it now would mean guessing at infrastructure that hasn't been asked for.

**Consequences:** Must be answered explicitly before Assessment Engine / API code (not part of this pass) is written.

---

## Still undefined — deliberately not invented

Per the original instruction not to invent diagnostic rules, weights, thresholds, severity mappings, recommendations, or proprietary decision logic, the following remain explicit, labeled gaps in the artifacts produced here (structurally stubbed as `null`, empty, or omitted — never filled with a guessed value):

- **Per-criterion severity rule** (`severity.rule`) — Spec §11 explicitly forbids deriving severity as a simple function of score; no alternative rule is given. Left `null` on every criterion.
- **Dimension/Journey/Priority aggregation logic** (`aggregation.dimension`, `.journey`, `.priority`) — Spec §13 calls this "proprietary diagnostic logic," explicitly undefined. Left `null`.
- **Finding-generation trigger logic** — what score/condition/pattern actually creates a finding, and of which type (`issue`/`opportunity`/`strength`). Not present in either document beyond the concept.
- **Priority precedence formula** — Spec §17 gives an ordered list of qualitative signals, not a scoring function or cutoffs.
- **Relationship/pattern map** — which criterion groupings form a "pattern" (Spec §15 gives two illustrative examples, not an exhaustive map) or count as an `explicit_relationship` for root-cause status (§18).
- **Recommendation copy** (`recommendations.json`) — does not exist in either document.
- **`finding_ref` naming convention** — Spec §23's one worked example uses `"audience_definition"` for the `audience` criterion (a `_definition` suffix), not just `"audience"`. Since only one example exists and it's a reference name rather than a scoring rule, `diagnostic.json` here standardizes on the criterion's own leaf slug (e.g. `"audience"`) for all 51 criteria, for consistency. This is a naming-convention choice, not business logic — flagging it in case the original suffix style was intentional and should be matched instead.
