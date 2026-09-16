"""
generate_findings()/generate_priorities() are no longer stubs -- their
rules are resolved in the frozen v1.0 definition (see findings.py,
priority.py). These tests now cover the one behavior that's still
relevant from the original stub era: what happens if a definition is
handed in with generation_rule/scoring_formula still literally "TBD"
(e.g. an older draft version, or a hand-modified definition in a
test). That must still raise clearly rather than silently guess.
"""

import unittest

from helpers import load_definition

from engine.errors import UndefinedDiagnosticRuleError
from engine.findings import generate_findings
from engine.priority import generate_priorities


class FindingGenerationRuleGuardTests(unittest.TestCase):
    def test_raises_if_generation_rule_is_tbd(self):
        definition = load_definition()
        definition["finding_model"]["generation_rule"] = "TBD"
        with self.assertRaises(UndefinedDiagnosticRuleError):
            generate_findings(definition, [])

    def test_raises_if_severity_derivation_rule_is_tbd(self):
        definition = load_definition()
        definition["severity_model"]["derivation_rule"] = "TBD"
        with self.assertRaises(UndefinedDiagnosticRuleError):
            generate_findings(definition, [])

    def test_frozen_definition_generation_rule_is_resolved(self):
        definition = load_definition()
        self.assertNotEqual(definition["finding_model"]["generation_rule"], "TBD")
        self.assertEqual(definition["finding_model"]["generation_rule"]["type"], "classification_mapping")


class PriorityScoringFormulaGuardTests(unittest.TestCase):
    def test_raises_if_scoring_formula_is_tbd(self):
        definition = load_definition()
        definition["priority"]["scoring_formula"] = "TBD"
        with self.assertRaises(UndefinedDiagnosticRuleError):
            generate_priorities(definition, [])

    def test_frozen_definition_scoring_formula_is_resolved(self):
        definition = load_definition()
        self.assertNotEqual(definition["priority"]["scoring_formula"], "TBD")
        self.assertEqual(definition["priority"]["scoring_formula"]["type"], "weighted_product")


if __name__ == "__main__":
    unittest.main()
