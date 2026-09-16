import unittest

from helpers import load_definition

from engine.errors import UnsupportedRuleTypeError
from engine.evaluate import evaluate_all_criteria, evaluate_criterion
from engine.types import Response


class EvaluateCriterionTests(unittest.TestCase):
    def setUp(self):
        self.definition = load_definition()
        self.criterion = self.definition["criteria"][0]  # attract.marketing_strategy.audience
        self.assertEqual(self.criterion["id"], "attract.marketing_strategy.audience")

    def test_each_maturity_band_maps_to_the_documented_classification(self):
        expected = {
            1: "needs_attention",
            2: "needs_attention",
            3: "developing",
            4: "strong",
            5: "operationalized",
        }
        for score, classification in expected.items():
            response = Response(self.criterion["id"], score, "e", "applicable")
            result = evaluate_criterion(self.criterion, response, self.definition)
            self.assertEqual(result.score, score)
            self.assertEqual(result.classification, classification)
            self.assertEqual(result.journey_stage, "attract")
            self.assertEqual(result.dimension, "marketing_strategy")
            self.assertIsNone(result.finding_id)

    def test_not_applicable_nulls_score_and_classification(self):
        response = Response(self.criterion["id"], None, "n/a", "not_applicable")
        result = evaluate_criterion(self.criterion, response, self.definition)
        self.assertIsNone(result.score)
        self.assertIsNone(result.classification)
        self.assertIsNone(result.finding_id)

    def test_unsupported_rule_type_raises(self):
        criterion = dict(self.criterion)
        criterion["evaluation"] = {"rule": {"type": "match"}}
        response = Response(criterion["id"], 3, "e", "applicable")
        with self.assertRaises(UnsupportedRuleTypeError):
            evaluate_criterion(criterion, response, self.definition)

    def test_evaluate_all_criteria_covers_every_criterion_exactly_once(self):
        responses = [
            Response(c["id"], 3, "e", "applicable") for c in self.definition["criteria"]
        ]
        results = evaluate_all_criteria(self.definition, responses)
        self.assertEqual(len(results), 51)
        ids = {r.criterion_id for r in results}
        self.assertEqual(ids, {c["id"] for c in self.definition["criteria"]})
        self.assertTrue(all(r.score == 3 for r in results))
        self.assertTrue(all(r.classification == "developing" for r in results))


if __name__ == "__main__":
    unittest.main()
