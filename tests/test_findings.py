import unittest

from helpers import load_definition

from engine.evaluate import evaluate_criterion
from engine.findings import generate_findings
from engine.types import Response


class FindingGenerationTests(unittest.TestCase):
    """classification_mapping (Design Spec section 10):
    needs_attention/developing -> issue, strong/operationalized -> strength,
    not_applicable -> no finding. No opportunity logic."""

    def setUp(self):
        self.definition = load_definition()
        self.criterion = self.definition["criteria"][0]  # attract.marketing_strategy.audience (impact=system)

    def _findings_for_value(self, value):
        response = Response(self.criterion["id"], value, "e", "applicable")
        cr = evaluate_criterion(self.criterion, response, self.definition)
        return generate_findings(self.definition, [cr])

    def test_needs_attention_and_developing_produce_issue(self):
        for value in (1, 2, 3):  # 1,2 -> needs_attention; 3 -> developing
            with self.subTest(value=value):
                findings = self._findings_for_value(value)
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].type, "issue")

    def test_strong_and_operationalized_produce_strength(self):
        for value in (4, 5):
            with self.subTest(value=value):
                findings = self._findings_for_value(value)
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].type, "strength")

    def test_no_opportunity_findings_are_ever_generated(self):
        for value in (1, 2, 3, 4, 5):
            findings = self._findings_for_value(value)
            self.assertNotEqual(findings[0].type, "opportunity")

    def test_not_applicable_produces_no_finding(self):
        response = Response(self.criterion["id"], None, "n/a", "not_applicable")
        cr = evaluate_criterion(self.criterion, response, self.definition)
        findings = generate_findings(self.definition, [cr])
        self.assertEqual(findings, [])

    def test_finding_ids_are_sequential_and_deterministic(self):
        responses = [Response(c["id"], 3, "e", "applicable") for c in self.definition["criteria"][:5]]
        crs = [evaluate_criterion(c, r, self.definition) for c, r in zip(self.definition["criteria"], responses)]
        findings1 = generate_findings(self.definition, crs)
        findings2 = generate_findings(self.definition, crs)
        self.assertEqual([f.finding_id for f in findings1], [f"F-{i:03d}" for i in range(1, 6)])
        self.assertEqual(findings1, findings2)


class SeverityMatrixTests(unittest.TestCase):
    """classification_impact_matrix (Design Spec section 11): severity is
    classification x criteria[*].impact, never score alone."""

    def setUp(self):
        self.definition = load_definition()
        by_id = {c["id"]: c for c in self.definition["criteria"]}
        # one real criterion per impact level, verified against the frozen definition
        self.by_impact = {
            "system": by_id["attract.marketing_strategy.audience"],
            "cross_journey": by_id["attract.systems_integration.tracking"],
            "journey": by_id["attract.marketing_strategy.acquisition"],
            "dimension": by_id["attract.marketing_strategy.positioning"],
            "criterion": by_id["attract.marketing_strategy.channels"],
        }
        for impact_level, criterion in self.by_impact.items():
            self.assertEqual(criterion["impact"], impact_level)

    def _severity(self, criterion, value):
        response = Response(criterion["id"], value, "e", "applicable")
        cr = evaluate_criterion(criterion, response, self.definition)
        findings = generate_findings(self.definition, [cr])
        return findings[0].severity if findings else None

    def test_needs_attention_severity_by_impact(self):
        expected = {"criterion": "low", "dimension": "moderate", "journey": "high", "cross_journey": "high", "system": "critical"}
        for impact, expected_severity in expected.items():
            with self.subTest(impact=impact):
                self.assertEqual(self._severity(self.by_impact[impact], 1), expected_severity)

    def test_developing_severity_by_impact(self):
        expected = {"criterion": "low", "dimension": "moderate", "journey": "high", "cross_journey": "high", "system": "high"}
        for impact, expected_severity in expected.items():
            with self.subTest(impact=impact):
                self.assertEqual(self._severity(self.by_impact[impact], 3), expected_severity)

    def test_strong_and_operationalized_have_no_severity_regardless_of_impact(self):
        for impact, criterion in self.by_impact.items():
            for value in (4, 5):
                with self.subTest(impact=impact, value=value):
                    self.assertIsNone(self._severity(criterion, value))

    def test_severity_is_not_a_pure_function_of_score_alone(self):
        # same score (1), different impact -> different severity: proves
        # severity isn't simply derived from the raw score (Design Spec section 11)
        low = self._severity(self.by_impact["criterion"], 1)
        critical = self._severity(self.by_impact["system"], 1)
        self.assertNotEqual(low, critical)


if __name__ == "__main__":
    unittest.main()
