import unittest

from helpers import load_definition

from engine.aggregate import aggregate_dimensions, aggregate_journey_stages
from engine.types import CriterionResult, Finding


class AggregateTests(unittest.TestCase):
    def setUp(self):
        self.definition = load_definition()
        self.criterion_results = [
            CriterionResult("attract.marketing_strategy.audience", "attract", "marketing_strategy", 2, "needs_attention", "F-001"),
            CriterionResult("attract.marketing_strategy.positioning", "attract", "marketing_strategy", 4, "strong", None),
            CriterionResult("attract.ux_design.landing_pages", "attract", "ux_design", 5, "operationalized", None),
            CriterionResult("engage.marketing_strategy.offer", "engage", "marketing_strategy", None, None, None),  # not_applicable
        ]
        self.findings = [
            Finding("F-001", "attract.marketing_strategy.audience", "attract", "marketing_strategy", "issue", "high"),
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
        # not_applicable criterion contributes to `criteria` but not to the distribution

        ux = dims["ux_design"]
        self.assertEqual(ux.criteria, ["attract.ux_design.landing_pages"])
        self.assertEqual(ux.classification_distribution, {"operationalized": 1})

        # dimensions with no criteria in this synthetic set still appear, empty
        self.assertIn("brand_identity", dims)
        self.assertEqual(dims["brand_identity"].criteria, [])
        self.assertEqual(dims["brand_identity"].classification_distribution, {})

    def test_journey_stage_grouping_and_distribution(self):
        journeys = aggregate_journey_stages(self.definition, self.criterion_results, self.findings)
        attract = journeys["attract"]
        self.assertEqual(len(attract.criteria), 3)
        self.assertEqual(attract.findings, ["F-001"])
        self.assertEqual(attract.classification_distribution, {"needs_attention": 1, "strong": 1, "operationalized": 1})

        engage = journeys["engage"]
        self.assertEqual(engage.criteria, ["engage.marketing_strategy.offer"])
        self.assertEqual(engage.classification_distribution, {})  # not_applicable, no classification

        self.assertIn("retain", journeys)
        self.assertEqual(journeys["retain"].criteria, [])

    def test_all_four_dimensions_and_journeys_always_present(self):
        dims = aggregate_dimensions(self.definition, [], [])
        journeys = aggregate_journey_stages(self.definition, [], [])
        self.assertEqual(set(dims.keys()), {"marketing_strategy", "ux_design", "brand_identity", "systems_integration"})
        self.assertEqual(set(journeys.keys()), {"attract", "engage", "convert", "retain"})


if __name__ == "__main__":
    unittest.main()
