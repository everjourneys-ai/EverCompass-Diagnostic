import unittest

from helpers import all_applicable_responses, load_definition

from engine.errors import (
    ContradictoryApplicabilityError,
    DuplicateResponseError,
    InvalidValueError,
    MissingResponseError,
    UnknownCriterionError,
    UnknownDiagnosticVersionError,
)
from engine.types import Response
from engine.validate import validate_responses


class ValidateResponsesTests(unittest.TestCase):
    def setUp(self):
        self.definition = load_definition()
        self.responses = all_applicable_responses(self.definition)

    def test_valid_full_response_set_passes(self):
        # should not raise
        validate_responses(self.definition, self.responses, self.definition["version"])

    def test_wrong_diagnostic_version_rejected(self):
        with self.assertRaises(UnknownDiagnosticVersionError):
            validate_responses(self.definition, self.responses, "9.9.9")

    def test_missing_response_rejected(self):
        missing_one = self.responses[1:]
        with self.assertRaises(MissingResponseError) as ctx:
            validate_responses(self.definition, missing_one, self.definition["version"])
        self.assertIn(self.responses[0].criterion_id, ctx.exception.details)

    def test_unknown_criterion_id_rejected(self):
        bad = list(self.responses) + [
            Response("not.a.real_criterion", 3, "evidence", "applicable")
        ]
        with self.assertRaises(UnknownCriterionError) as ctx:
            validate_responses(self.definition, bad, self.definition["version"])
        self.assertIn("not.a.real_criterion", ctx.exception.details)

    def test_duplicate_response_rejected(self):
        dup = list(self.responses) + [self.responses[0]]
        with self.assertRaises(DuplicateResponseError) as ctx:
            validate_responses(self.definition, dup, self.definition["version"])
        self.assertIn(self.responses[0].criterion_id, ctx.exception.details)

    def test_invalid_value_zero_rejected(self):
        bad = list(self.responses)
        bad[0] = Response(bad[0].criterion_id, 0, "evidence", "applicable")
        with self.assertRaises(InvalidValueError):
            validate_responses(self.definition, bad, self.definition["version"])

    def test_invalid_value_six_rejected(self):
        bad = list(self.responses)
        bad[0] = Response(bad[0].criterion_id, 6, "evidence", "applicable")
        with self.assertRaises(InvalidValueError):
            validate_responses(self.definition, bad, self.definition["version"])

    def test_invalid_value_non_integer_rejected(self):
        bad = list(self.responses)
        bad[0] = Response(bad[0].criterion_id, 3.5, "evidence", "applicable")
        with self.assertRaises(InvalidValueError):
            validate_responses(self.definition, bad, self.definition["version"])

    def test_valid_value_boundaries_accepted(self):
        for boundary in (1, 5):
            responses = list(self.responses)
            responses[0] = Response(responses[0].criterion_id, boundary, "evidence", "applicable")
            validate_responses(self.definition, responses, self.definition["version"])

    def test_not_applicable_with_null_value_accepted(self):
        responses = list(self.responses)
        responses[0] = Response(responses[0].criterion_id, None, "not used", "not_applicable")
        validate_responses(self.definition, responses, self.definition["version"])

    def test_not_applicable_with_non_null_value_rejected(self):
        bad = list(self.responses)
        bad[0] = Response(bad[0].criterion_id, 3, "evidence", "not_applicable")
        with self.assertRaises(ContradictoryApplicabilityError) as ctx:
            validate_responses(self.definition, bad, self.definition["version"])
        self.assertIn(bad[0].criterion_id, ctx.exception.details)


if __name__ == "__main__":
    unittest.main()
