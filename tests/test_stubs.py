import unittest

from helpers import load_definition

from engine.errors import UndefinedDiagnosticRuleError
from engine.findings import generate_findings
from engine.priority import generate_priorities


class FindingStubTests(unittest.TestCase):
    def test_returns_empty_while_generation_rule_is_tbd(self):
        definition = load_definition()
        self.assertEqual(definition["finding_model"]["generation_rule"], "TBD")
        self.assertEqual(generate_findings(definition, []), [])

    def test_raises_loudly_if_rule_defined_without_code_update(self):
        definition = load_definition()
        definition["finding_model"]["generation_rule"] = {"some": "future-defined rule"}
        with self.assertRaises(UndefinedDiagnosticRuleError):
            generate_findings(definition, [])


class PriorityStubTests(unittest.TestCase):
    def test_returns_empty_while_scoring_formula_is_tbd(self):
        definition = load_definition()
        self.assertEqual(definition["priority"]["scoring_formula"], "TBD")
        self.assertEqual(generate_priorities(definition, []), [])

    def test_raises_loudly_if_rule_defined_without_code_update(self):
        definition = load_definition()
        definition["priority"]["scoring_formula"] = {"some": "future-defined rule"}
        with self.assertRaises(UndefinedDiagnosticRuleError):
            generate_priorities(definition, [])


if __name__ == "__main__":
    unittest.main()
