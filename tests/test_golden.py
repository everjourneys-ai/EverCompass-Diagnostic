"""
Golden test runner. See tests/golden/GOLDEN_TEST_SPEC.md for format
and coverage. The engine is now implemented (finding generation,
severity, dimension/journey aggregation, concentration, priority) --
full-assessment-tier fixtures get real field-by-field comparisons.
Concentration is fixed at "isolated" for v1.0 (semantic grouping
deferred, see src/engine/concentration.py), so no "competing priority
candidates" fixture exists -- see GOLDEN_TEST_SPEC.md's Known Gap.
"""

import glob
import json
import os
import unittest

from helpers import load_definition

from engine import errors as engine_errors
from engine.engine import evaluate
from engine.types import Response

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden", "fixtures")

VALID_DOMINANT_CONDITIONS = {"critical", "high", "moderate", "developing", "strong", "operationalized", "no_data"}
VALID_JOURNEY_STAGES = {"attract", "engage", "convert", "retain"}
VALID_DIMENSIONS = {"marketing_strategy", "ux_design", "brand_identity", "systems_integration"}


def load_fixtures():
    fixtures = {}
    for path in sorted(glob.glob(os.path.join(FIXTURES_DIR, "*.json"))):
        with open(path) as f:
            fixture = json.load(f)
        fixtures[fixture["name"]] = fixture
    return fixtures


def to_responses(raw_responses):
    return [
        Response(
            criterion_id=r["criterion_id"],
            value=r["value"],
            evidence=r["evidence"],
            applicability=r["applicability"],
        )
        for r in raw_responses
    ]


def assert_matches_result_shape(test, result):
    """Lightweight, dependency-free structural check against
    schema/result.schema.json's shape -- no subprocess/npx dependency
    in the committed test suite. Full schema validation of a fixture's
    expected_result was already done with ajv-cli while authoring it."""
    required_top = {
        "assessment_id", "diagnostic_id", "diagnostic_version", "engine_version",
        "criterion_results", "findings", "dimensions", "journey_stages",
        "priorities", "system_summary",
    }
    test.assertTrue(required_top <= set(result.keys()), result.keys())
    test.assertNotIn("overall_score", result, "ADR-009: no overall score, ever")

    test.assertEqual(set(result["dimensions"].keys()), VALID_DIMENSIONS)
    test.assertEqual(set(result["journey_stages"].keys()), VALID_JOURNEY_STAGES)
    for group in list(result["dimensions"].values()) + list(result["journey_stages"].values()):
        test.assertIn("dominant_condition", group)
        test.assertIn(group["dominant_condition"], VALID_DOMINANT_CONDITIONS)
        test.assertIn("classification_distribution", group["summary"])


class ValidationTierGoldenTests(unittest.TestCase):
    """Fixtures with expect == 'error'. These pass today -- validate_responses()
    raises before the engine ever reaches the unimplemented findings/priority stage."""

    @classmethod
    def setUpClass(cls):
        cls.definition = load_definition()
        cls.fixtures = {n: f for n, f in load_fixtures().items() if f["expect"] == "error"}

    def test_all_error_fixtures_raise_the_expected_error_type(self):
        self.assertGreater(len(self.fixtures), 0, "no error-tier fixtures found")
        for name, fixture in self.fixtures.items():
            with self.subTest(fixture=name):
                responses = to_responses(fixture["responses"])
                expected_cls = getattr(engine_errors, fixture["expected_error"])
                with self.assertRaises(expected_cls):
                    evaluate(self.definition, responses, f"asm_{name}", fixture["diagnostic_version"])


class FullAssessmentTierGoldenTests(unittest.TestCase):
    """Fixtures with expect == 'result'. The engine now implements finding
    generation, severity, dimension/journey aggregation, concentration, and
    priority scoring/ordering -- these fixtures get a full field-by-field
    comparison against the real evaluate() output."""

    @classmethod
    def setUpClass(cls):
        cls.definition = load_definition()
        cls.fixtures = {n: f for n, f in load_fixtures().items() if f["expect"] == "result"}

    def test_at_least_one_full_assessment_fixture_exists(self):
        self.assertGreater(len(self.fixtures), 0, "no result-tier fixtures found")

    def test_every_fixtures_expected_result_matches_result_shape(self):
        """Fixture self-consistency check -- independent of engine state."""
        for name, fixture in self.fixtures.items():
            with self.subTest(fixture=name):
                assert_matches_result_shape(self, fixture["expected_result"])

    def test_full_assessment_fixtures_against_the_current_engine(self):
        from engine.serialize import to_dict

        for name, fixture in self.fixtures.items():
            with self.subTest(fixture=name):
                responses = to_responses(fixture["responses"])
                result = evaluate(self.definition, responses, f"asm_{name}", fixture["diagnostic_version"])
                actual = to_dict(result)
                expected = fixture["expected_result"]
                for key in (
                    "criterion_results", "findings", "dimensions", "journey_stages",
                    "priorities", "system_summary",
                ):
                    self.assertEqual(actual[key], expected[key], f"{name}: {key} mismatch")


class GoldenFixtureInventoryTests(unittest.TestCase):
    """Confirms the fixture set matches what GOLDEN_TEST_SPEC.md claims to ship."""

    def test_fixture_count_and_names(self):
        fixtures = load_fixtures()
        expected_names = {
            "invalid_value_zero", "invalid_value_six", "missing_response",
            "duplicate_response", "contradictory_not_applicable", "unknown_criterion",
            "wrong_diagnostic_version",
            "full_all_needs_attention", "full_all_operationalized",
            "full_single_weak_criterion", "full_concentrated_marketing_strategy",
            "full_critical_finding", "full_multiple_high_findings", "full_not_applicable",
        }
        self.assertEqual(set(fixtures.keys()), expected_names)
        self.assertEqual(len(fixtures), 14)


if __name__ == "__main__":
    unittest.main()
