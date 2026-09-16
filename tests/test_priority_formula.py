import unittest

from helpers import load_definition

from engine.priority import compute_priority_score, generate_priorities
from engine.types import Finding


class PriorityFormulaTests(unittest.TestCase):
    """priority_score = severity_weight x impact_weight x concentration_weight
    x journey_relevance_weight (all four tables read from
    priority.scoring_formula). journey_relevance_weight is 3 for every v1
    criterion (uniformly "high") and concentration_weight is 1 (isolated,
    Decision 1) -- both asserted explicitly here, not just assumed."""

    def setUp(self):
        self.definition = load_definition()
        formula = self.definition["priority"]["scoring_formula"]
        self.assertEqual(formula["journey_relevance_weights"]["high"], 3)
        self.assertEqual(formula["concentration_weights"]["isolated"], 1)
        # every criterion is uniformly journey_relevance = "high" in v1.0
        self.assertTrue(all(c["journey_relevance"] == "high" for c in self.definition["criteria"]))

    def test_formula_matches_hand_computation_for_known_impact_severity_pairs(self):
        # severity_weights: low=1 moderate=2 high=3 critical=4
        # impact_weights: criterion=1 dimension=2 journey=3 cross_journey=4 system=5
        # concentration_weight fixed at 1 (isolated) x journey_relevance_weight fixed at 3
        cases = [
            ("attract.marketing_strategy.channels", "low", 1 * 1 * 1 * 3),        # criterion impact
            ("attract.marketing_strategy.positioning", "moderate", 2 * 2 * 1 * 3),  # dimension impact
            ("attract.marketing_strategy.acquisition", "high", 3 * 3 * 1 * 3),      # journey impact
            ("attract.systems_integration.tracking", "high", 3 * 4 * 1 * 3),        # cross_journey impact
            ("attract.marketing_strategy.audience", "critical", 4 * 5 * 1 * 3),     # system impact
        ]
        for criterion_id, severity, expected_score in cases:
            with self.subTest(criterion_id=criterion_id, severity=severity):
                finding = Finding("F-001", criterion_id, "attract", "marketing_strategy", "issue", severity)
                score = compute_priority_score(self.definition, finding, concentration_weight=1)
                self.assertEqual(score, expected_score)

    def test_max_theoretical_score_is_reachable_in_principle(self):
        # critical(4) x system(5) x systemic(4, not used in v1) x critical(4, not used in v1) = 320
        formula = self.definition["priority"]["scoring_formula"]
        computed_max = (
            max(formula["severity_weights"].values())
            * max(formula["impact_weights"].values())
            * max(formula["concentration_weights"].values())
            * max(formula["journey_relevance_weights"].values())
        )
        self.assertEqual(computed_max, formula["max_theoretical_score"])
        self.assertEqual(computed_max, 320)

    def test_only_issue_findings_become_priorities(self):
        findings = [
            Finding("F-001", "attract.marketing_strategy.audience", "attract", "marketing_strategy", "issue", "critical"),
            Finding("F-002", "attract.marketing_strategy.positioning", "attract", "marketing_strategy", "strength", None),
        ]
        priorities = generate_priorities(self.definition, findings)
        self.assertEqual(len(priorities), 1)
        self.assertEqual(priorities[0].supporting_findings, ["F-001"])

    def test_deterministic_ordering_by_score_descending_with_criterion_id_tiebreak(self):
        # two findings with equal priority_score (same severity+impact) --
        # must break the tie deterministically by criterion_id, not input order
        findings = [
            Finding("F-001", "attract.marketing_strategy.channels", "attract", "marketing_strategy", "issue", "low"),
            Finding("F-002", "engage.marketing_strategy.content_strategy", "engage", "marketing_strategy", "issue", "low"),
        ]
        priorities_a = generate_priorities(self.definition, findings)
        priorities_b = generate_priorities(self.definition, list(reversed(findings)))
        self.assertEqual(
            [p.supporting_findings[0] for p in priorities_a],
            [p.supporting_findings[0] for p in priorities_b],
        )
        # attract.* sorts before engage.* lexicographically
        self.assertEqual(priorities_a[0].supporting_findings, ["F-001"])

    def test_priority_ids_are_renumbered_in_final_sorted_order(self):
        findings = [
            Finding("F-001", "attract.marketing_strategy.channels", "attract", "marketing_strategy", "issue", "low"),
            Finding("F-002", "attract.marketing_strategy.audience", "attract", "marketing_strategy", "issue", "critical"),
        ]
        priorities = generate_priorities(self.definition, findings)
        self.assertEqual(priorities[0].priority_id, "P-001")
        self.assertEqual(priorities[0].supporting_findings, ["F-002"])  # critical outranks low
        self.assertEqual(priorities[1].priority_id, "P-002")


if __name__ == "__main__":
    unittest.main()
