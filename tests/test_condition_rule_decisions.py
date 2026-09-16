"""
Tests for the three methodology decisions finalized this session:

1. A single High finding must produce a High condition (no 2+ threshold,
   no high-impact-criterion special case -- HIGH now works exactly like
   CRITICAL: any qualifying finding is enough).
2. Journey aggregation operates over applicable dimensions only
   (dimensions with zero applicable criteria are excluded from the
   count). "Most" is a strict majority of applicable dimensions,
   scaled by how many are applicable (1->1, 2->2, 3->2, 4->3).
   "Multiple" stays a fixed 2+, unscaled. All four dimensions with
   zero applicable criteria -> journey "no_data".
3. OPERATIONALIZED is reachable and stronger than STRONG: all
   applicable dimensions/criteria must be Operationalized (not just a
   majority) with no meaningful issues, and is evaluated BEFORE STRONG
   in the precedence order (critical, high, moderate, developing,
   operationalized, strong).

These tests are written against the NEW rules and are expected to FAIL
until diagnostic.json and the engine are both updated -- see the
session's commit history for before/after.
"""

import unittest

from helpers import load_definition

from engine.aggregate import aggregate_dimensions, aggregate_journey_stages
from engine.types import CriterionResult, Finding


class SingleHighFindingTests(unittest.TestCase):
    def setUp(self):
        self.definition = load_definition()

    def test_single_high_finding_dimension_resolves_to_high(self):
        # attract.systems_integration.tracking: impact=cross_journey,
        # developing -> high severity. Only ONE such finding, nothing else
        # qualifies for CRITICAL/HIGH via any other predicate.
        criterion_results = [
            CriterionResult("attract.systems_integration.tracking", "attract", "systems_integration", 3, "developing", "F-001"),
            CriterionResult("attract.systems_integration.attribution", "attract", "systems_integration", 5, "operationalized", None),
        ]
        findings = [
            Finding("F-001", "attract.systems_integration.tracking", "attract", "systems_integration", "issue", "high"),
        ]
        dims = aggregate_dimensions(self.definition, criterion_results, findings)
        self.assertEqual(dims["systems_integration"].dominant_condition, "high")

    def test_single_high_finding_journey_resolves_to_high(self):
        criterion_results = [
            CriterionResult("engage.brand_identity.trust", "engage", "brand_identity", 3, "developing", "F-001"),
            CriterionResult("engage.brand_identity.clarity", "engage", "brand_identity", 5, "operationalized", None),
        ]
        # trust: impact=journey, developing -> high severity
        findings = [
            Finding("F-001", "engage.brand_identity.trust", "engage", "brand_identity", "issue", "high"),
        ]
        journeys = aggregate_journey_stages(self.definition, criterion_results, findings)
        self.assertEqual(journeys["engage"].dominant_condition, "high")


class PartialJourneyCoverageTests(unittest.TestCase):
    """'Most' = strict majority of applicable dimensions: 1->1, 2->2, 3->2, 4->3."""

    def setUp(self):
        self.definition = load_definition()

    def _all_strong(self, criterion_ids_by_dim):
        criterion_results = []
        for dim, crit_id in criterion_ids_by_dim.items():
            criterion_results.append(CriterionResult(crit_id, "convert", dim, 4, "strong", None))
        return criterion_results

    def test_one_applicable_dimension_most_is_one(self):
        # only ux_design has data; a single strong criterion should be
        # enough to satisfy "most (=1 of 1) dimensions are strong or
        # better" for the journey.
        criterion_results = self._all_strong({"ux_design": "convert.ux_design.forms"})
        journeys = aggregate_journey_stages(self.definition, criterion_results, [])
        self.assertEqual(journeys["convert"].dominant_condition, "strong")

    def test_two_applicable_dimensions_most_is_two(self):
        criterion_results = self._all_strong({
            "ux_design": "convert.ux_design.forms",
            "brand_identity": "convert.brand_identity.credibility",
        })
        journeys = aggregate_journey_stages(self.definition, criterion_results, [])
        self.assertEqual(journeys["convert"].dominant_condition, "strong")

    def test_three_applicable_dimensions_most_is_two_of_three(self):
        # 2 of 3 applicable dimensions strong-or-better should be enough
        # (strict majority of 3 = 2) -- the third is developing (not
        # strong-or-better, and not enough alone to flip MODERATE/DEVELOPING
        # since "multiple" for those rules is a fixed 2+, and only 1
        # dimension is weak here).
        criterion_results = [
            CriterionResult("convert.ux_design.forms", "convert", "ux_design", 4, "strong", None),
            CriterionResult("convert.brand_identity.credibility", "convert", "brand_identity", 5, "operationalized", None),
            CriterionResult("convert.marketing_strategy.offer", "convert", "marketing_strategy", 3, "developing", "F-001"),
        ]
        findings = [
            Finding("F-001", "convert.marketing_strategy.offer", "convert", "marketing_strategy", "issue", "moderate"),
        ]
        journeys = aggregate_journey_stages(self.definition, criterion_results, findings)
        self.assertEqual(journeys["convert"].dominant_condition, "strong")

    def test_all_four_dimensions_zero_applicable_is_no_data(self):
        criterion_results = [
            CriterionResult("convert.ux_design.forms", "convert", "ux_design", None, None, None),
        ]
        journeys = aggregate_journey_stages(self.definition, criterion_results, [])
        self.assertEqual(journeys["convert"].dominant_condition, "no_data")


class OperationalizedTests(unittest.TestCase):
    def setUp(self):
        self.definition = load_definition()

    def test_all_applicable_criteria_operationalized_dimension_resolves_to_operationalized(self):
        criterion_results = [
            CriterionResult(f"attract.ux_design.{slug}", "attract", "ux_design", 5, "operationalized", None)
            for slug in ("discovery_experience", "landing_pages", "entry_points")
        ]
        dims = aggregate_dimensions(self.definition, criterion_results, [])
        self.assertEqual(dims["ux_design"].dominant_condition, "operationalized")

    def test_all_applicable_dimensions_operationalized_journey_resolves_to_operationalized(self):
        criterion_results = [
            CriterionResult("convert.ux_design.forms", "convert", "ux_design", 5, "operationalized", None),
            CriterionResult("convert.brand_identity.credibility", "convert", "brand_identity", 5, "operationalized", None),
        ]
        journeys = aggregate_journey_stages(self.definition, criterion_results, [])
        self.assertEqual(journeys["convert"].dominant_condition, "operationalized")

    def test_operationalized_does_not_collapse_into_strong(self):
        """The core Decision 3 regression check: 100% operationalized data
        must resolve to 'operationalized', never fall through to 'strong'
        because STRONG's weaker condition is checked first."""
        criterion_results = [
            CriterionResult(f"attract.ux_design.{slug}", "attract", "ux_design", 5, "operationalized", None)
            for slug in ("discovery_experience", "landing_pages", "entry_points")
        ]
        dims = aggregate_dimensions(self.definition, criterion_results, [])
        self.assertNotEqual(dims["ux_design"].dominant_condition, "strong")
        self.assertEqual(dims["ux_design"].dominant_condition, "operationalized")

    def test_majority_but_not_all_operationalized_resolves_to_strong_not_operationalized(self):
        """One non-operationalized (but still strong-or-better) criterion
        is enough to keep the dimension out of OPERATIONALIZED (which
        needs ALL applicable, not just a majority) while still landing
        on STRONG."""
        criterion_results = [
            CriterionResult("attract.ux_design.discovery_experience", "attract", "ux_design", 5, "operationalized", None),
            CriterionResult("attract.ux_design.landing_pages", "attract", "ux_design", 5, "operationalized", None),
            CriterionResult("attract.ux_design.entry_points", "attract", "ux_design", 4, "strong", None),
        ]
        dims = aggregate_dimensions(self.definition, criterion_results, [])
        self.assertEqual(dims["ux_design"].dominant_condition, "strong")


if __name__ == "__main__":
    unittest.main()
