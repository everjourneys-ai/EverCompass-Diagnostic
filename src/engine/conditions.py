"""
Generic condition_rules interpreter for dimension/journey aggregation
(Design Spec v1.0 sections 13-14, resolved as declarative data in
aggregation.dimension.method / aggregation.journey.method).

Dispatches entirely on each predicate's "type" string, as given in
definition["aggregation"][...]["method"]["condition_rules"]. No
EverCompass-specific criterion IDs or business rules are hardcoded
here -- everything comes from the definition. Adding a new predicate
type later means adding a new branch to _eval_predicate, not
rewriting this module's structure.

Journey Insufficient Data (Decision 2, this session):
  - All 4 dimensions have zero applicable criteria -> journey "no_data".
  - 1-3 dimensions have zero applicable criteria -> evaluate using only
    the dimensions that have data. No special status, no confidence
    penalty, no new threshold.
"""

from __future__ import annotations

from .errors import UndefinedDiagnosticRuleError
from .types import CriterionResult, Finding


def _compare(a, op: str, b) -> bool:
    return {">=": a >= b, ">": a > b, "<=": a <= b, "<": a < b, "==": a == b}[op]


def _eval_predicate(pred: dict, ctx: dict) -> bool:
    """
    ctx keys used (only the ones a given predicate type needs):
      group_cr: list[CriterionResult] in this group
      group_f:  list[Finding] in this group
      applicable_count: int
      by_id: dict[criterion_id -> criterion definition] (for impact lookup)
      dims_in_journey: dict[dimension_id -> dominant_condition] (journey scope only)
    """
    t = pred["type"]

    if t == "has_finding_with_severity":
        return any(f.severity == pred["severity"] for f in ctx["group_f"])

    if t == "count_findings_with_severity":
        n = sum(1 for f in ctx["group_f"] if f.severity == pred["severity"])
        return _compare(n, pred["operator"], pred["value"])

    if t == "has_finding_with_severity_on_high_impact_criterion":
        qualifies = set(pred["high_impact_criterion_definition"]["qualifies"])
        for f in ctx["group_f"]:
            if f.severity == pred["severity"] and ctx["by_id"][f.criterion_id]["impact"] in qualifies:
                return True
        return False

    if t == "percentage_of_applicable_in_classifications":
        applicable = ctx["applicable_count"]
        if applicable == 0:
            return False
        n = sum(1 for cr in ctx["group_cr"] if cr.classification in pred["classifications"])
        return _compare(n / applicable, pred["operator"], pred["value"])

    if t == "no_finding_with_severity_in":
        return not any(f.severity in pred["severities"] for f in ctx["group_f"])

    if t == "no_meaningful_issues":
        finding_type = pred["meaningful_issues_definition"]["finding_type"]
        return not any(f.type == finding_type for f in ctx["group_f"])

    if t == "count_dimensions_with_finding_severity":
        dims = {f.dimension for f in ctx["group_f"] if f.severity == pred["severity"]}
        return _compare(len(dims), pred["operator"], pred["value"])

    if t == "count_dimensions_with_meaningful_weakness":
        classes = set(pred["meaningful_weakness_definition"]["criterion_classifications"])
        dims = {cr.dimension for cr in ctx["group_cr"] if cr.classification in classes}
        return _compare(len(dims), pred["operator"], pred["value"])

    if t == "count_dimensions_with_condition":
        dims_in_journey = ctx["dims_in_journey"]
        n = sum(1 for cond in dims_in_journey.values() if cond == pred["condition"])
        return _compare(n, pred["operator"], pred["value"])

    if t == "count_dimensions_at_or_above_condition":
        dims_in_journey = ctx["dims_in_journey"]
        qualifying = set(pred["conditions"])
        n = sum(1 for cond in dims_in_journey.values() if cond in qualifying)
        return _compare(n, pred["operator"], pred["value"])

    if t == "count_dimensions_at_condition":
        dims_in_journey = ctx["dims_in_journey"]
        n = sum(1 for cond in dims_in_journey.values() if cond == pred["condition"])
        return _compare(n, pred["operator"], pred["value"])

    if t == "all_applicable_dimensions_at_condition":
        # Decision 3: ALL applicable dimensions (those not "no_data") must
        # equal the given condition. Vacuously false if there are no
        # applicable dimensions at all -- callers short-circuit that case
        # to "no_data" before condition_rules ever runs (see
        # journey_dominant_condition), so this should never actually see
        # an all-no_data dims_in_journey in practice.
        dims_in_journey = ctx["dims_in_journey"]
        applicable = [cond for cond in dims_in_journey.values() if cond != "no_data"]
        return bool(applicable) and all(cond == pred["condition"] for cond in applicable)

    if t == "majority_of_applicable_dimensions_at_or_above_condition":
        # Decision 2: "most" = a strict majority of *applicable* dimensions
        # (those not "no_data"), scaled by how many are applicable --
        # floor(applicable_count / 2) + 1. This is generic arithmetic (the
        # standard definition of "strict majority"), not EverCompass-specific
        # business logic; a future diagnostic version could reuse this
        # predicate type with entirely different qualifying conditions.
        dims_in_journey = ctx["dims_in_journey"]
        applicable = [cond for cond in dims_in_journey.values() if cond != "no_data"]
        applicable_count = len(applicable)
        if applicable_count == 0:
            return False
        required = applicable_count // 2 + 1
        qualifying = set(pred["conditions"])
        n = sum(1 for cond in applicable if cond in qualifying)
        return n >= required

    raise NotImplementedError(f"unknown condition predicate type: {t!r}")


def evaluate_condition_rules(condition_rules: list[dict], ctx: dict) -> str:
    """
    Evaluate condition_rules top to bottom (already the definition's own
    order -- critical first); the first rule whose predicates match
    (per its "match": "any"/"all") wins. Callers handle the "no_data"
    (zero/insufficient applicable data) case before calling this --
    condition_rules itself has no zero-data branch, by design (Design
    Spec's rules assume there is data to evaluate).

    KNOWN GAP, discovered during implementation, not invented around:
    the six condition_rules are not actually exhaustive over every
    possible input. E.g. exactly one high-severity finding (or exactly
    one moderate) with everything else clean matches neither HIGH
    (needs 2+ occurrences) nor STRONG (requires zero high/critical
    findings anywhere in scope) -- reproducible with real 51-criterion
    data, not just sparse test fixtures. This is a real coverage gap in
    the frozen v1.0 methodology's condition_rules, the same category of
    thing as the concentration-grouping and journey-insufficient-data
    gaps resolved earlier this session -- not something this
    interpreter should paper over by guessing which of the six tiers
    is "closest". It fails loudly and specifically instead.
    """
    for rule in condition_rules:
        results = [_eval_predicate(p, ctx) for p in rule["conditions"]]
        matched = any(results) if rule["match"] == "any" else all(results)
        if matched:
            return rule["condition"]
    raise UndefinedDiagnosticRuleError(
        "No condition_rules entry matched this group's findings/classifications. "
        "The six-tier rule set (critical..operationalized) is not exhaustive over "
        "every possible input -- see this function's docstring. This is a gap in "
        "the frozen methodology's condition_rules, not a bug in this interpreter; "
        "it requires a methodology decision (a new rule or an explicit fallback), "
        "not an engineering guess."
    )


def dimension_dominant_condition(
    definition: dict,
    group_cr: list[CriterionResult],
    group_f: list[dict],
) -> str:
    applicable = sum(1 for cr in group_cr if cr.score is not None)
    if applicable == 0:
        return definition["aggregation"]["dimension"]["method"]["zero_applicable_criteria"]["condition"]

    by_id = {c["id"]: c for c in definition["criteria"]}
    ctx = {"group_cr": group_cr, "group_f": group_f, "applicable_count": applicable, "by_id": by_id}
    rules = definition["aggregation"]["dimension"]["method"]["condition_rules"]
    return evaluate_condition_rules(rules, ctx)


def journey_dominant_condition(
    definition: dict,
    journey_cr: list[CriterionResult],
    journey_f: list[dict],
    dims_in_journey: dict[str, str],
) -> str:
    """
    dims_in_journey: each of the journey's 4 dimensions' dominant
    condition, computed over ONLY that journey's slice of the
    dimension (not the dimension's global, cross-journey result --
    those are a different computation; see aggregate.py).

    Decision 2 (this session): "no_data" only when ALL 4 are
    "no_data" (i.e. zero applicable criteria journey-wide). Otherwise,
    evaluate normally using whatever dimensions have data -- dimensions
    with "no_data" simply don't match any of the count/percentage
    predicates above, so they're naturally excluded, not specially
    flagged.
    """
    if all(cond == "no_data" for cond in dims_in_journey.values()):
        return "no_data"

    applicable = sum(1 for cr in journey_cr if cr.score is not None)
    by_id = {c["id"]: c for c in definition["criteria"]}
    ctx = {
        "group_cr": journey_cr, "group_f": journey_f, "applicable_count": applicable,
        "by_id": by_id, "dims_in_journey": dims_in_journey,
    }
    rules = definition["aggregation"]["journey"]["method"]["condition_rules"]
    return evaluate_condition_rules(rules, ctx)
