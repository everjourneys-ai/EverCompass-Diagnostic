import unittest

from helpers import load_definition

from engine.aggregate import aggregate_dimensions, aggregate_journey_stages
from engine.errors import UndefinedDiagnosticRuleError
from engine.types import CriterionResult, Finding


class AggregateTests(unittest.TestCase):
    def setUp(self):
        self.definition = load_definition()
        # attract.marketing_strategy.audience has impact=system in the real
        # frozen definition -- needs_attention there is a critical-severity
        # finding, which resolves both its dimension and journey via the
        # unambiguous "any critical finding" rule regardless of how sparse
        # the rest of this synthetic set is. (An earlier version of this
        # fixture used a lone *high*-severity finding, which turned out to
        # hit a real gap in the frozen condition_rules -- see
        # test_journey_condition_rules_gap_is_not_silently_guessed below.)
        self.criterion_results = [
            CriterionResult("attract.marketing_strategy.audience", "attract", "marketing_strategy", 1, "needs_attention", "F-001"),
            CriterionResult("attract.marketing_strategy.positioning", "attract", "marketing_strategy", 4, "strong", None),
            CriterionResult("attract.ux_design.landing_pages", "attract", "ux_design", 5, "operationalized", None),
            CriterionResult("engage.marketing_strategy.offer", "engage", "marketing_strategy", None, None, None),  # not_applicable
        ]
        self.findings = [
            Finding("F-001", "attract.marketing_strategy.audience", "attract", "marketing_strategy", "issue", "critical"),
        ]

    def test_dimension_grouping_and_distribution(self):
        dims = aggregate_dimensions(self.definition, self.criterion_results, self.findings)
        ms = dims["marketing_strategy"]
        self.assertEqual(
            set(ms.criteria),
            {"attract.marketing_strategy.audience", "attract.marketing_strategy.positioning", "engage.marketing_strategy.offer"},
        )
        self.assertEqual(ms.findings, ["F-001"])
        self.assertEqual(ms.classification_distribution, {"needs_attention": 1, "strong": 1})
        self.assertEqual(ms.dominant_condition, "critical")  # any critical finding
        # not_applicable criterion contributes to `criteria` but not to the distribution

        ux = dims["ux_design"]
        self.assertEqual(ux.criteria, ["attract.ux_design.landing_pages"])
        self.assertEqual(ux.classification_distribution, {"operationalized": 1})
        self.assertEqual(ux.dominant_condition, "strong")  # majority strong-or-better, no high/critical findings here

        # dimensions with no criteria in this synthetic set still appear, empty
        self.assertIn("brand_identity", dims)
        self.assertEqual(dims["brand_identity"].criteria, [])
        self.assertEqual(dims["brand_identity"].classification_distribution, {})
        self.assertEqual(dims["brand_identity"].dominant_condition, "no_data")

    def test_journey_stage_grouping_and_distribution(self):
        journeys = aggregate_journey_stages(self.definition, self.criterion_results, self.findings)
        attract = journeys["attract"]
        self.assertEqual(len(attract.criteria), 3)
        self.assertEqual(attract.findings, ["F-001"])
        self.assertEqual(attract.classification_distribution, {"needs_attention": 1, "strong": 1, "operationalized": 1})
        self.assertEqual(attract.dominant_condition, "critical")  # any critical finding, propagates from marketing_strategy

        engage = journeys["engage"]
        self.assertEqual(engage.criteria, ["engage.marketing_strategy.offer"])
        self.assertEqual(engage.classification_distribution, {})  # not_applicable, no classification
        self.assertEqual(engage.dominant_condition, "no_data")  # its one criterion is not_applicable -> zero applicable

        self.assertIn("retain", journeys)
        self.assertEqual(journeys["retain"].criteria, [])
        self.assertEqual(journeys["retain"].dominant_condition, "no_data")

    def test_all_four_dimensions_and_journeys_always_present(self):
        dims = aggregate_dimensions(self.definition, [], [])
        journeys = aggregate_journey_stages(self.definition, [], [])
        self.assertEqual(set(dims.keys()), {"marketing_strategy", "ux_design", "brand_identity", "systems_integration"})
        self.assertEqual(set(journeys.keys()), {"attract", "engage", "convert", "retain"})
        self.assertTrue(all(v.dominant_condition == "no_data" for v in dims.values()))
        self.assertTrue(all(v.dominant_condition == "no_data" for v in journeys.values()))

    def test_journey_partial_data_evaluates_using_available_dimensions_only(self):
        """
        Decision 2 (this session, final for v1.0): if 1-3 of a journey's 4
        dimensions have zero applicable criteria, do NOT create a special
        insufficient-data status -- evaluate using only the dimensions that
        have data. No confidence penalty, no new threshold. Only when ALL 4
        are zero does the journey resolve to "no_data".

        Uses a finding-COUNT-based rule (2+ moderate findings) rather than
        a dimension-COUNT-based one deliberately -- see
        test_journey_condition_rules_gap_is_not_silently_guessed and
        test_operationalized_tier_is_unreachable_given_the_frozen_rule_order:
        several dimension-count-based rules turn out not to scale down
        cleanly when fewer than 4 dimensions have data, which is a separate,
        already-documented finding, not what this test is checking.
        """
        # convert: only marketing_strategy and brand_identity have any data
        # (2 of 4 dimensions); ux_design and systems_integration are
        # entirely absent, not just not_applicable.
        criterion_results = [
            CriterionResult("convert.marketing_strategy.offer", "convert", "marketing_strategy", 3, "developing", "F-001"),
            CriterionResult("convert.brand_identity.value_communication", "convert", "brand_identity", 3, "developing", "F-002"),
        ]
        # both criteria have impact=dimension -> developing x dimension = moderate severity
        findings = [
            Finding("F-001", "convert.marketing_strategy.offer", "convert", "marketing_strategy", "issue", "moderate"),
            Finding("F-002", "convert.brand_identity.value_communication", "convert", "brand_identity", "issue", "moderate"),
        ]
        journeys = aggregate_journey_stages(self.definition, criterion_results, findings)
        convert = journeys["convert"]
        # Resolves normally (moderate, via "2+ moderate findings") using
        # only the 2 populated dimensions -- NOT "no_data", even though
        # half the journey's dimensions are entirely empty.
        self.assertEqual(convert.dominant_condition, "moderate")

    def test_journey_all_four_dimensions_zero_applicable_is_no_data(self):
        criterion_results = [
            CriterionResult("convert.ux_design.forms", "convert", "ux_design", None, None, None),  # not_applicable
        ]
        journeys = aggregate_journey_stages(self.definition, criterion_results, [])
        self.assertEqual(journeys["convert"].dominant_condition, "no_data")

    def test_journey_condition_rules_gap_is_not_silently_guessed(self):
        """
        Real, discovered gap in the frozen v1.0 methodology (not a bug
        here): a journey with exactly one high-severity finding and
        everything else clean matches neither HIGH (needs 2+
        occurrences) nor STRONG (requires zero high/critical findings
        anywhere in the journey) -- reproducible with full, realistic
        51-criterion data, not just this sparse synthetic set (verified
        separately against the real engine during implementation). The
        interpreter must fail loudly and specifically rather than guess
        which of the six tiers is "closest".
        """
        criterion_results = [
            CriterionResult("engage.brand_identity.trust", "engage", "brand_identity", 3, "developing", "F-001"),
            CriterionResult("engage.brand_identity.clarity", "engage", "brand_identity", 5, "operationalized", None),
        ]
        # trust has impact=journey in the real definition -> developing x journey = high severity
        findings = [
            Finding("F-001", "engage.brand_identity.trust", "engage", "brand_identity", "issue", "high"),
        ]
        with self.assertRaises(UndefinedDiagnosticRuleError):
            aggregate_journey_stages(self.definition, criterion_results, findings)

    def test_operationalized_tier_is_unreachable_given_the_frozen_rule_order(self):
        """
        Real, discovered gap in the frozen v1.0 methodology (not a bug
        here, and not something this test invents a fix for): STRONG's
        condition ("majority of applicable criteria are Strong or better
        AND no High or Critical findings") is a strict superset of what
        triggers OPERATIONALIZED ("majority ... Operationalized AND no
        meaningful issues") -- every population that would satisfy
        OPERATIONALIZED also trivially satisfies STRONG's weaker
        condition, and STRONG is evaluated first in the given precedence
        order (critical -> high -> moderate -> developing -> strong ->
        operationalized). So OPERATIONALIZED can never actually be
        reached for any input, at either the dimension or journey level,
        as literally specified. Verified here with a dimension where
        100% of applicable criteria are answered "operationalized" --
        the correct-per-the-frozen-rules result is still "strong".
        """
        criterion_results = [
            CriterionResult(f"attract.ux_design.{slug}", "attract", "ux_design", 5, "operationalized", None)
            for slug in ("discovery_experience", "landing_pages", "entry_points")
        ]
        dims = aggregate_dimensions(self.definition, criterion_results, [])
        self.assertEqual(dims["ux_design"].dominant_condition, "strong")
        self.assertEqual(dims["ux_design"].classification_distribution, {"operationalized": 3})


if __name__ == "__main__":
    unittest.main()
