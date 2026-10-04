import tempfile
import unittest
from pathlib import Path

from decision_system import (
    ClosedLoopProductionDecisionSystem,
    GreedyFallbackPlanner,
    JsonlAuditStore,
    ProductInput,
    ProductionSnapshot,
)


class FailingPlanner:
    def solve(self, snapshot):
        raise RuntimeError("simulated solver outage")


class TestProductionDecisionSystem(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.audit = JsonlAuditStore(Path(self.tmp.name) / "audit.jsonl")
        self.snapshot = ProductionSnapshot(
            planning_key="plant/test",
            available_capacity=8,
            products=(
                ProductInput("A", 6, 1.0, 1.0, 10.0),
                ProductInput("B", 6, 1.0, 1.0, 8.0),
            ),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_data_contract_rejects_duplicate_products(self):
        bad = ProductionSnapshot(
            planning_key="x",
            available_capacity=10,
            products=(
                ProductInput("A", 1, 1, 1, 1),
                ProductInput("A", 2, 1, 1, 1),
            ),
        )
        with self.assertRaises(ValueError):
            bad.validate()

    def test_primary_plan_respects_capacity(self):
        system = ClosedLoopProductionDecisionSystem(self.audit)
        decision = system.recommend(self.snapshot)
        used = sum(
            p.unit_capacity * decision.result.production[p.product_id]
            for p in self.snapshot.products
        )
        self.assertLessEqual(used, self.snapshot.available_capacity + 1e-9)
        self.assertFalse(decision.used_fallback)

    def test_fallback_is_audited(self):
        system = ClosedLoopProductionDecisionSystem(
            self.audit,
            primary_planner=FailingPlanner(),
            fallback_planner=GreedyFallbackPlanner(),
        )
        decision = system.recommend(self.snapshot)
        self.assertTrue(decision.used_fallback)
        events = self.audit.read_all()
        self.assertEqual(events[-1]["event_type"], "recommendation")
        self.assertIsNotNone(events[-1]["primary_failure"])

    def test_human_override_requires_reason(self):
        system = ClosedLoopProductionDecisionSystem(self.audit)
        decision = system.recommend(self.snapshot)
        with self.assertRaises(ValueError):
            system.apply_human_override(decision, {"A": 4}, reason="")

    def test_drift_triggers_reoptimization(self):
        system = ClosedLoopProductionDecisionSystem(
            self.audit,
            drift_threshold=0.20,
        )
        decision = system.recommend(self.snapshot)
        feedback = system.record_execution(
            decision,
            forecast_demand={"A": 6, "B": 6},
            actual_demand={"A": 10, "B": 8},
        )
        self.assertTrue(feedback["reoptimization_required"])


if __name__ == "__main__":
    unittest.main()
