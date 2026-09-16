import unittest

from helpers import all_applicable_responses, load_definition, varied_responses

from engine.engine import ENGINE_VERSION, evaluate
from engine.errors import UnknownDiagnosticVersionError
from engine.serialize import to_dict
from engine.types import Response


class EndToEndEngineTests(unittest.TestCase):
    def setUp(self):
        self.definition = load_definition()

    def test_determinism_same_inputs_same_output(self):
        responses = varied_responses(self.definition)
        r1 = evaluate(self.definition, responses, "asm_test_001", self.definition["version"])
        r2 = evaluate(self.definition, responses, "asm_test_001", self.definition["version"])
        self.assertEqual(to_dict(r1), to_dict(r2))

    def test_full_assessment_shape(self):
        responses = varied_responses(self.definition)
        result = evaluate(self.definition, responses, "asm_test_002", self.definition["version"])

        self.assertEqual(result.assessment_id, "asm_test_002")
        self.assertEqual(result.diagnostic_id, "evercompass")
        self.assertEqual(result.diagnostic_version, "1.0.0")
        self.assertEqual(result.engine_version, ENGINE_VERSION)
        self.assertEqual(len(result.criterion_results), 51)

        # varied_responses() cycles 1-5, so every classification band is hit
        # -- findings and priorities are real now that the engine is implemented.
        self.assertEqual(len(result.findings), 51)  # every criterion is applicable -> one finding each
        self.assertGreater(len(result.priorities), 0)
        self.assertTrue(all(p.priority_score > 0 for p in result.priorities))
        # priorities are exactly the issue-type findings (needs_attention/developing)
        issue_findings = [f for f in result.findings if f.type == "issue"]
        self.assertEqual(len(result.priorities), len(issue_findings))
        # sorted by priority_score descending
        scores = [p.priority_score for p in result.priorities]
        self.assertEqual(scores, sorted(scores, reverse=True))

        self.assertEqual(set(result.dimensions.keys()), {"marketing_strategy", "ux_design", "brand_identity", "systems_integration"})
        self.assertEqual(set(result.journey_stages.keys()), {"attract", "engage", "convert", "retain"})
        self.assertTrue(all(agg.dominant_condition != "" for agg in result.dimensions.values()))
        self.assertTrue(all(agg.dominant_condition != "" for agg in result.journey_stages.values()))

        # every criterion is accounted for exactly once across dimensions,
        # and exactly once across journey stages
        dim_criteria = [c for agg in result.dimensions.values() for c in agg.criteria]
        journey_criteria = [c for agg in result.journey_stages.values() for c in agg.criteria]
        self.assertEqual(sorted(dim_criteria), sorted(c["id"] for c in self.definition["criteria"]))
        self.assertEqual(sorted(journey_criteria), sorted(c["id"] for c in self.definition["criteria"]))

        self.assertEqual(result.system_summary.criteria_total, 51)
        self.assertEqual(result.system_summary.criteria_applicable, 51)
        self.assertEqual(result.system_summary.criteria_not_applicable, 0)
        self.assertEqual(result.system_summary.findings_total, 51)
        self.assertEqual(result.system_summary.priority_count, len(result.priorities))

    def test_not_applicable_criteria_excluded_from_applicable_count(self):
        responses = all_applicable_responses(self.definition, value=4)
        na_id = "convert.ux_design.checkout"
        responses = [
            r if r.criterion_id != na_id else Response(na_id, None, "we do not sell online", "not_applicable")
            for r in responses
        ]
        result = evaluate(self.definition, responses, "asm_test_003", self.definition["version"])

        self.assertEqual(result.system_summary.criteria_applicable, 50)
        self.assertEqual(result.system_summary.criteria_not_applicable, 1)

        checkout_result = next(cr for cr in result.criterion_results if cr.criterion_id == na_id)
        self.assertIsNone(checkout_result.score)
        self.assertIsNone(checkout_result.classification)
        self.assertIsNone(checkout_result.finding_id)

        # the not_applicable criterion is still listed under its dimension/journey,
        # just excluded from the classification_distribution tally
        convert_ux = result.dimensions["ux_design"]
        self.assertIn(na_id, convert_ux.criteria)

    def test_wrong_diagnostic_version_is_rejected_end_to_end(self):
        responses = all_applicable_responses(self.definition)
        with self.assertRaises(UnknownDiagnosticVersionError):
            evaluate(self.definition, responses, "asm_test_004", "0.0.1")

    def test_serialized_output_matches_result_schema_shape(self):
        responses = varied_responses(self.definition)
        result = evaluate(self.definition, responses, "asm_test_005", self.definition["version"])
        d = to_dict(result)
        self.assertEqual(
            set(d.keys()),
            {
                "assessment_id", "diagnostic_id", "diagnostic_version", "engine_version",
                "criterion_results", "findings", "dimensions", "journey_stages",
                "priorities", "system_summary",
            },
        )
        self.assertNotIn("overall_score", d)  # ADR-009: no overall score, ever


if __name__ == "__main__":
    unittest.main()
