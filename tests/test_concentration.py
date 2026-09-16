import unittest

from helpers import load_definition

from engine.concentration import determine_concentration
from engine.types import Finding


class ConcentrationTests(unittest.TestCase):
    """Decision 1 (this session, final for v1.0): semantic related-finding
    grouping is deferred. Every finding is its own isolated group of one --
    never inferred from journey, dimension, criterion type, impact,
    severity, or any combination."""

    def setUp(self):
        self.definition = load_definition()

    def test_always_isolated_regardless_of_other_findings_present(self):
        f1 = Finding("F-001", "attract.marketing_strategy.audience", "attract", "marketing_strategy", "issue", "critical")
        f2 = Finding("F-002", "attract.marketing_strategy.positioning", "attract", "marketing_strategy", "issue", "moderate")
        f3 = Finding("F-003", "attract.systems_integration.tracking", "attract", "systems_integration", "issue", "high")

        # same journey, same dimension, same severity tier as others present --
        # none of that should matter; still isolated
        for target in (f1, f2, f3):
            with self.subTest(finding=target.finding_id):
                result = determine_concentration(target, [f1, f2, f3], self.definition)
                self.assertEqual(result.concentration, "isolated")
                self.assertEqual(result.related_finding_ids, [target.finding_id])

    def test_weight_matches_the_definitions_isolated_weight(self):
        f = Finding("F-001", "attract.marketing_strategy.audience", "attract", "marketing_strategy", "issue", "critical")
        result = determine_concentration(f, [f], self.definition)
        expected_weight = self.definition["priority"]["scoring_formula"]["concentration_weights"]["isolated"]
        self.assertEqual(result.weight, expected_weight)
        self.assertEqual(result.weight, 1)

    def test_relationship_rules_extension_point_is_not_silently_used(self):
        f = Finding("F-001", "attract.marketing_strategy.audience", "attract", "marketing_strategy", "issue", "critical")
        with self.assertRaises(NotImplementedError):
            determine_concentration(f, [f], self.definition, relationship_rules={"anything": True})


if __name__ == "__main__":
    unittest.main()
