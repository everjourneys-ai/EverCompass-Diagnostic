"""
Property/invariant tests -- Pre-API Hardening Pass (Phase 11).

These validate structural guarantees the architecture/methodology already
requires, but that no existing test asserted directly:

- the diagnostic definition is a fixed input, never mutated by evaluate()
  (Design Spec section 24: a published definition is immutable; Architecture
  v1.2 section 3: the engine is a pure function).
- changing one response changes only the criterion results, findings, and
  dimension/journey groups that criterion actually belongs to -- nothing
  else in the result moves.
- criterion_id is unique across the definition (implied by every lookup in
  the engine treating criterion_id as a primary key -- evaluate.py,
  findings.py, priority.py all build `{c["id"]: c for c in ...}` dicts).
- every criterion names exactly one journey_stage and one dimension, and
  both are members of the definition's own enumerated journey_stages/
  dimensions lists (the two independent axes DECISIONS.md ADR-014
  describes).

No new methodology is asserted here -- only structure and determinism
already required by the frozen definition and the engine's own docstrings.
"""

from __future__ import annotations

import copy
import unittest

from helpers import load_definition, varied_responses

from engine.engine import evaluate
from engine.serialize import to_dict
from engine.types import Response


class DefinitionImmutabilityTests(unittest.TestCase):
    def test_evaluate_does_not_mutate_the_definition(self):
        definition = load_definition()
        before = copy.deepcopy(definition)
        responses = varied_responses(definition)
        evaluate(definition, responses, "asm_immutability", definition["version"])
        self.assertEqual(definition, before)


class CriterionResponseIsolationTests(unittest.TestCase):
    """Changing one response must only move the result data that
    criterion actually feeds -- its own criterion_result/finding, and the
    dimension/journey groups it belongs to. Everything else must be
    byte-identical to a baseline run."""

    def setUp(self):
        self.definition = load_definition()

    def test_changing_one_response_only_affects_its_own_criterion_and_groups(self):
        baseline_responses = varied_responses(self.definition)
        baseline = to_dict(evaluate(self.definition, baseline_responses, "asm_a", self.definition["version"]))

        target = self.definition["criteria"][0]
        target_id = target["id"]
        target_dimension = target["dimension"]
        target_journey = target["journey_stage"]

        by_id_baseline = {r.criterion_id: r for r in baseline_responses}
        changed_responses = [
            Response(
                cid,
                by_id_baseline[cid].value if cid != target_id else (by_id_baseline[cid].value % 5) + 1,
                by_id_baseline[cid].evidence,
                by_id_baseline[cid].applicability,
            )
            for cid in by_id_baseline
        ]
        changed = to_dict(evaluate(self.definition, changed_responses, "asm_a", self.definition["version"]))

        # every OTHER criterion_result is untouched
        baseline_by_id = {cr["criterion_id"]: cr for cr in baseline["criterion_results"]}
        changed_by_id = {cr["criterion_id"]: cr for cr in changed["criterion_results"]}
        for cid in baseline_by_id:
            if cid == target_id:
                continue
            self.assertEqual(baseline_by_id[cid], changed_by_id[cid], f"unrelated criterion {cid} changed")

        # every dimension/journey NOT containing the target criterion is untouched
        for dim_id, group in baseline["dimensions"].items():
            if dim_id == target_dimension:
                continue
            self.assertEqual(group, changed["dimensions"][dim_id], f"unrelated dimension {dim_id} changed")
        for journey_id, group in baseline["journey_stages"].items():
            if journey_id == target_journey:
                continue
            self.assertEqual(group, changed["journey_stages"][journey_id], f"unrelated journey {journey_id} changed")


class DefinitionStructuralInvariantTests(unittest.TestCase):
    def setUp(self):
        self.definition = load_definition()

    def test_criterion_ids_are_unique(self):
        ids = [c["id"] for c in self.definition["criteria"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_criterion_maps_to_exactly_one_journey_and_dimension(self):
        valid_journeys = {j["id"] for j in self.definition["journey_stages"]}
        valid_dimensions = {d["id"] for d in self.definition["dimensions"]}
        for c in self.definition["criteria"]:
            self.assertIsInstance(c["journey_stage"], str)
            self.assertIsInstance(c["dimension"], str)
            self.assertIn(c["journey_stage"], valid_journeys)
            self.assertIn(c["dimension"], valid_dimensions)


if __name__ == "__main__":
    unittest.main()
