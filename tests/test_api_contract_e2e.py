"""
End-to-end contract test (Phase 1 API task, section 11):

    Frontend request -> FastAPI -> Application Layer -> Assessment Engine
    -> Structured Result -> JSON response

Runs the real TestClient against the real app (real DiagnosticRepository
loading the real src/definitions/diagnostic.json, real application layer,
real engine -- nothing mocked), verifies the resulting JSON has the
correct structural shape (the same check test_golden.py uses against
schema/result.schema.json's shape), and verifies it matches a real Golden
Test fixture's expected_result field-by-field (everything except
assessment_id, which is application-layer-generated per request, not
part of the engine's own deterministic output -- see test_api_assess.py::
ValidAssessmentTests::test_two_calls_generate_distinct_assessment_ids).
"""

import glob
import json
import os
import unittest

from api_helpers import make_client
from helpers import load_definition

from test_golden import VALID_DIMENSIONS, VALID_JOURNEY_STAGES, assert_matches_result_shape

_FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "golden", "fixtures", "full_critical_finding.json"
)


class EndToEndContractTests(unittest.TestCase):
    def setUp(self):
        self.client = make_client()
        self.definition = load_definition()
        with open(_FIXTURE_PATH) as f:
            self.fixture = json.load(f)

    def test_full_request_to_json_response_matches_golden_fixture(self):
        response = self.client.post(
            "/api/v1/diagnostics/evercompass/assess",
            json={
                "diagnostic_version": self.fixture["diagnostic_version"],
                "responses": self.fixture["responses"],
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()

        # structural conformance to schema/result.schema.json's shape
        # (same check the committed golden-test suite uses -- see
        # test_golden.py's own docstring for why it avoids a live
        # subprocess/npx ajv dependency in the committed suite; a real
        # ajv-cli run against a live response was performed manually as
        # part of this task's final validation pass).
        assert_matches_result_shape(self, body)
        self.assertEqual(set(body["dimensions"].keys()), VALID_DIMENSIONS)
        self.assertEqual(set(body["journey_stages"].keys()), VALID_JOURNEY_STAGES)

        # field-by-field match against the golden fixture, excluding
        # assessment_id (see module docstring)
        expected = self.fixture["expected_result"]
        for key in ("criterion_results", "findings", "dimensions", "journey_stages", "priorities", "system_summary"):
            self.assertEqual(body[key], expected[key], f"{key} mismatch")
        self.assertEqual(body["diagnostic_id"], expected["diagnostic_id"])
        self.assertEqual(body["diagnostic_version"], expected["diagnostic_version"])

    def test_all_full_assessment_fixtures_round_trip_through_the_api(self):
        """Broader sweep: every full-assessment golden fixture, not just
        one, produces the same result through the API as through calling
        the engine directly (test_golden.py already proves the latter)."""
        for path in sorted(glob.glob(os.path.join(os.path.dirname(_FIXTURE_PATH), "full_*.json"))):
            with open(path) as f:
                fixture = json.load(f)
            with self.subTest(fixture=fixture["name"]):
                response = self.client.post(
                    "/api/v1/diagnostics/evercompass/assess",
                    json={"diagnostic_version": fixture["diagnostic_version"], "responses": fixture["responses"]},
                )
                self.assertEqual(response.status_code, 200)
                body = response.json()
                expected = fixture["expected_result"]
                for key in ("criterion_results", "findings", "dimensions", "journey_stages", "priorities", "system_summary"):
                    self.assertEqual(body[key], expected[key], f"{fixture['name']}: {key} mismatch")


if __name__ == "__main__":
    unittest.main()
