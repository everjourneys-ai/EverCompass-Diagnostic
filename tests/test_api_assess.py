"""
POST /api/v1/diagnostics/{id}/assess -- the real deterministic engine
runs end to end for every test here (no mocking); see test_api_contract_e2e.py
for the primary end-to-end contract test against schema/result.schema.json
and a golden fixture.
"""

import copy
import unittest

from api_helpers import make_client, valid_response_payload
from helpers import load_definition


class ValidAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.client = make_client()
        self.definition = load_definition()

    def test_valid_assessment_returns_200_with_full_result_shape(self):
        payload = {"diagnostic_version": "1.0.0", "responses": valid_response_payload(self.definition)}
        response = self.client.post("/api/v1/diagnostics/evercompass/assess", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            set(body.keys()),
            {
                "assessment_id", "diagnostic_id", "diagnostic_version", "engine_version",
                "criterion_results", "findings", "dimensions", "journey_stages",
                "priorities", "system_summary",
            },
        )
        self.assertEqual(body["diagnostic_id"], "evercompass")
        self.assertEqual(body["diagnostic_version"], "1.0.0")
        self.assertEqual(len(body["criterion_results"]), 51)
        self.assertNotIn("overall_score", body)

    def test_two_calls_generate_distinct_assessment_ids(self):
        payload = {"diagnostic_version": "1.0.0", "responses": valid_response_payload(self.definition)}
        r1 = self.client.post("/api/v1/diagnostics/evercompass/assess", json=payload)
        r2 = self.client.post("/api/v1/diagnostics/evercompass/assess", json=payload)
        self.assertNotEqual(r1.json()["assessment_id"], r2.json()["assessment_id"])
        # everything except assessment_id is identical (the engine itself
        # is still a pure function of the same definition + responses --
        # only assessment_id is application-layer-generated per request)
        b1, b2 = dict(r1.json()), dict(r2.json())
        del b1["assessment_id"], b2["assessment_id"]
        self.assertEqual(b1, b2)


class AssessValidationErrorTests(unittest.TestCase):
    def setUp(self):
        self.client = make_client()
        self.definition = load_definition()
        self.responses = valid_response_payload(self.definition)

    def _post(self, responses, diagnostic_version="1.0.0"):
        return self.client.post(
            "/api/v1/diagnostics/evercompass/assess",
            json={"diagnostic_version": diagnostic_version, "responses": responses},
        )

    def test_missing_response_returns_400(self):
        response = self._post(self.responses[1:])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "missing_response")

    def test_unknown_criterion_returns_400(self):
        bad = copy.deepcopy(self.responses)
        bad.append({"criterion_id": "not.a.real_criterion", "value": 3, "evidence": "e", "applicability": "applicable"})
        response = self._post(bad)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "unknown_criterion")

    def test_invalid_value_returns_400(self):
        bad = copy.deepcopy(self.responses)
        bad[0]["value"] = 9
        response = self._post(bad)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_value")

    def test_duplicate_response_returns_400(self):
        bad = copy.deepcopy(self.responses) + [copy.deepcopy(self.responses[0])]
        response = self._post(bad)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "duplicate_response")

    def test_contradictory_applicability_returns_400(self):
        bad = copy.deepcopy(self.responses)
        bad[0]["applicability"] = "not_applicable"
        bad[0]["value"] = 3  # contradiction: not_applicable but non-null value
        response = self._post(bad)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "contradictory_applicability")

    def test_unknown_diagnostic_returns_404(self):
        response = self.client.post(
            "/api/v1/diagnostics/not-a-real-diagnostic/assess",
            json={"diagnostic_version": "1.0.0", "responses": self.responses},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "unknown_diagnostic")

    def test_unknown_version_returns_404(self):
        response = self._post(self.responses, diagnostic_version="9.9.9")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "unknown_diagnostic_version")

    def test_malformed_request_missing_required_field_returns_400(self):
        response = self.client.post(
            "/api/v1/diagnostics/evercompass/assess",
            json={"responses": self.responses},  # missing diagnostic_version
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "malformed_request")

    def test_malformed_request_wrong_type_returns_400(self):
        response = self.client.post(
            "/api/v1/diagnostics/evercompass/assess",
            json={"diagnostic_version": "1.0.0", "responses": "not-a-list"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "malformed_request")

    def test_malformed_request_not_json_returns_400(self):
        response = self.client.post(
            "/api/v1/diagnostics/evercompass/assess",
            content=b"not json at all",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "malformed_request")

    def test_error_response_never_contains_a_python_traceback(self):
        response = self._post(self.responses[1:])
        text = response.text
        self.assertNotIn("Traceback", text)
        self.assertNotIn(".py", text)


if __name__ == "__main__":
    unittest.main()
