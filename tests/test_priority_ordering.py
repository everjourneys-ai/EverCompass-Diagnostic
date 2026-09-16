import unittest

from engine.priority import PrioritySignals, order_priorities
from engine.types import Priority


def _priority(pid: str) -> Priority:
    return Priority(pid, f"title-{pid}", [], [], [])


class OrderPrioritiesTests(unittest.TestCase):
    def test_severity_tier_precedence(self):
        # Design Spec section 17, tiers 1/3/5/6 (broad-impact/concentration
        # variants covered separately below)
        critical = PrioritySignals(_priority("critical"), "critical", False, False, 0, 0, 0)
        high = PrioritySignals(_priority("high"), "high", False, False, 0, 0, 0)
        moderate = PrioritySignals(_priority("moderate"), "moderate", False, False, 0, 0, 0)
        low = PrioritySignals(_priority("low"), "low", False, False, 0, 0, 0)

        ordered = order_priorities([low, moderate, high, critical])
        self.assertEqual([p.priority_id for p in ordered], ["critical", "high", "moderate", "low"])

    def test_high_with_broad_impact_outranks_plain_high(self):
        high_broad = PrioritySignals(_priority("high_broad"), "high", True, False, 0, 0, 0)
        high_plain = PrioritySignals(_priority("high_plain"), "high", False, False, 0, 0, 0)
        ordered = order_priorities([high_plain, high_broad])
        self.assertEqual([p.priority_id for p in ordered], ["high_broad", "high_plain"])

    def test_moderate_with_concentration_outranks_plain_moderate(self):
        mod_concentrated = PrioritySignals(_priority("mod_c"), "moderate", False, True, 0, 0, 0)
        mod_plain = PrioritySignals(_priority("mod_p"), "moderate", False, False, 0, 0, 0)
        ordered = order_priorities([mod_plain, mod_concentrated])
        self.assertEqual([p.priority_id for p in ordered], ["mod_c", "mod_p"])

    def test_tie_break_order_relationship_then_concentration_then_journey_relevance(self):
        # all critical severity -- tie-breaks decide order
        a = PrioritySignals(_priority("a"), "critical", False, False, explicit_relationship_breadth=2, concentration=1, journey_relevance=1)
        b = PrioritySignals(_priority("b"), "critical", False, False, explicit_relationship_breadth=1, concentration=5, journey_relevance=5)
        ordered = order_priorities([b, a])
        # a wins on relationship_breadth (2 > 1) despite lower concentration/relevance
        self.assertEqual([p.priority_id for p in ordered], ["a", "b"])

        c = PrioritySignals(_priority("c"), "critical", False, False, explicit_relationship_breadth=1, concentration=1, journey_relevance=9)
        d = PrioritySignals(_priority("d"), "critical", False, False, explicit_relationship_breadth=1, concentration=3, journey_relevance=1)
        ordered2 = order_priorities([c, d])
        # equal relationship_breadth -> concentration decides
        self.assertEqual([p.priority_id for p in ordered2], ["d", "c"])

    def test_stable_sort_preserves_input_order_for_true_ties(self):
        x = PrioritySignals(_priority("x"), "low", False, False, 0, 0, 0)
        y = PrioritySignals(_priority("y"), "low", False, False, 0, 0, 0)
        ordered = order_priorities([x, y])
        self.assertEqual([p.priority_id for p in ordered], ["x", "y"])


if __name__ == "__main__":
    unittest.main()
