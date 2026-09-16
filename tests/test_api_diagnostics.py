"""
GET /api/v1/diagnostics and GET /api/v1/diagnostics/{id}, including the
public/internal data boundary check (Phase 1 API task, section 8): the
public diagnostic response must not leak any proprietary rule
expression, threshold, weight, or internal decision logic.
"""

import unittest

from api_helpers import make_client
from helpers import load_definition

#: Internal-only keys that must never appear anywhere in the public
#: diagnostic response, at any nesting level. Chosen from
#: src/definitions/diagnostic.json's own top-level and per-criterion
#: keys that carry methodology (not structural/display content).
_INTERNAL_ONLY_KEYS = {
    "severity_model",
    "finding_model",
    "aggregation",
    "priority",
    "rule_types",
    "impact_model",
    "journey_relevance_model",
    "impact",
    "journey_relevance",
    "evaluation",
    "severity",
    "finding",
    "condition_rules",
    "scoring_formula",
    "generation_rule",
    "derivation_rule",
}


def _collect_keys(value, found: set) -> None:
    if isinstance(value, dict):
        for key, sub in value.items():
            found.add(key)
            _collect_keys(sub, found)
    elif isinstance(value, list):
        for item in value:
            _collect_keys(item, found)


class DiagnosticsListTests(unittest.TestCase):
    def test_list_returns_only_discovery_metadata(self):
        client = make_client()
        response = client.get("/api/v1/diagnostics")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        entry = body[0]
        self.assertEqual(set(entry.keys()), {"diagnostic_id", "name", "version", "status"})
        self.assertEqual(entry["diagnostic_id"], "evercompass")
        self.assertEqual(entry["version"], "1.0.0")
        self.assertEqual(entry["status"], "published")


class DiagnosticDetailTests(unittest.TestCase):
    def setUp(self):
        self.client = make_client()
        self.definition = load_definition()

    def test_returns_all_51_criteria_with_public_fields(self):
        response = self.client.get("/api/v1/diagnostics/evercompass")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["criteria"]), 51)
        criterion = body["criteria"][0]
        self.assertEqual(set(criterion.keys()), {"id", "journey_stage", "dimension", "question", "response_type"})
        self.assertEqual(len(body["journey_stages"]), 4)
        self.assertEqual(len(body["dimensions"]), 4)
        self.assertEqual(len(body["response_scale"]), 5)

    def test_unknown_diagnostic_returns_404(self):
        response = self.client.get("/api/v1/diagnostics/not-a-real-diagnostic")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "unknown_diagnostic")

    def test_public_response_does_not_expose_proprietary_rule_internals(self):
        """Phase 1 API task section 8/14: the public diagnostic endpoint
        must not leak internal rule expressions, thresholds, weights,
        priority formulas, or finding-generation/decision logic."""
        response = self.client.get("/api/v1/diagnostics/evercompass")
        body = response.json()

        found_keys: set = set()
        _collect_keys(body, found_keys)
        leaked = found_keys & _INTERNAL_ONLY_KEYS
        self.assertEqual(leaked, set(), f"internal-only keys leaked into public response: {leaked}")

        # the raw internal definition genuinely contains all of these --
        # this proves the check above is discriminating, not vacuous.
        internal_keys: set = set()
        _collect_keys(self.definition, internal_keys)
        self.assertTrue(_INTERNAL_ONLY_KEYS <= internal_keys)


if __name__ == "__main__":
    unittest.main()
