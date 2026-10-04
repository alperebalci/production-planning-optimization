"""Closed-loop production decision system reference implementation.

This module demonstrates the engineering layer around a prescriptive model:
data contracts, optimization, fallbacks, auditability, human override, execution
feedback, and drift-triggered reoptimization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping, Protocol
from uuid import uuid4

import pulp


@dataclass(frozen=True)
class ProductInput:
    product_id: str
    forecast_demand: float
    unit_capacity: float
    production_cost: float
    backlog_penalty: float

    def validate(self) -> None:
        if not self.product_id:
            raise ValueError("product_id must not be empty")
        if self.forecast_demand < 0:
            raise ValueError("forecast_demand must be non-negative")
        if self.unit_capacity <= 0:
            raise ValueError("unit_capacity must be positive")
        if self.production_cost < 0:
            raise ValueError("production_cost must be non-negative")
        if self.backlog_penalty < 0:
            raise ValueError("backlog_penalty must be non-negative")


@dataclass(frozen=True)
class ProductionSnapshot:
    products: tuple[ProductInput, ...]
    available_capacity: float
    planning_key: str

    def validate(self) -> None:
        if not self.planning_key:
            raise ValueError("planning_key must not be empty")
        if self.available_capacity < 0:
            raise ValueError("available_capacity must be non-negative")
        if not self.products:
            raise ValueError("at least one product is required")

        seen: set[str] = set()
        for product in self.products:
            product.validate()
            if product.product_id in seen:
                raise ValueError(f"duplicate product_id: {product.product_id}")
            seen.add(product.product_id)

    def canonical_payload(self) -> dict:
        return {
            "planning_key": self.planning_key,
            "available_capacity": self.available_capacity,
            "products": [asdict(p) for p in self.products],
        }


@dataclass(frozen=True)
class PlanResult:
    production: dict[str, int]
    backlog: dict[str, float]
    objective: float
    planner: str
    status: str


class Planner(Protocol):
    def solve(self, snapshot: ProductionSnapshot) -> PlanResult:
        ...


class MilpProductionPlanner:
    """Primary planner using a small capacity-constrained production MILP."""

    def __init__(self, time_limit_seconds: int = 10) -> None:
        self.time_limit_seconds = time_limit_seconds

    def solve(self, snapshot: ProductionSnapshot) -> PlanResult:
        snapshot.validate()
        model = pulp.LpProblem("closed_loop_production_plan", pulp.LpMinimize)

        production = {
            p.product_id: pulp.LpVariable(
                f"produce_{p.product_id}",
                lowBound=0,
                cat=pulp.LpInteger,
            )
            for p in snapshot.products
        }
        backlog = {
            p.product_id: pulp.LpVariable(
                f"backlog_{p.product_id}",
                lowBound=0,
                cat=pulp.LpContinuous,
            )
            for p in snapshot.products
        }

        model += pulp.lpSum(
            p.production_cost * production[p.product_id]
            + p.backlog_penalty * backlog[p.product_id]
            for p in snapshot.products
        )

        model += (
            pulp.lpSum(
                p.unit_capacity * production[p.product_id]
                for p in snapshot.products
            )
            <= snapshot.available_capacity
        )

        for p in snapshot.products:
            model += (
                production[p.product_id] + backlog[p.product_id]
                >= p.forecast_demand
            )

        solver = pulp.PULP_CBC_CMD(
            msg=False,
            timeLimit=self.time_limit_seconds,
        )
        model.solve(solver)
        status = pulp.LpStatus.get(model.status, str(model.status))

        if status not in {"Optimal", "Integer Feasible", "Feasible"}:
            raise RuntimeError(f"primary planner status={status}")

        production_out = {
            p.product_id: int(round(production[p.product_id].value() or 0.0))
            for p in snapshot.products
        }
        backlog_out = {
            p.product_id: float(backlog[p.product_id].value() or 0.0)
            for p in snapshot.products
        }
        return PlanResult(
            production=production_out,
            backlog=backlog_out,
            objective=float(pulp.value(model.objective) or 0.0),
            planner="milp",
            status=status,
        )


class GreedyFallbackPlanner:
    """Deterministic fallback used when the primary optimization path fails."""

    def solve(self, snapshot: ProductionSnapshot) -> PlanResult:
        snapshot.validate()
        remaining = float(snapshot.available_capacity)
        production = {p.product_id: 0 for p in snapshot.products}

        ranked = sorted(
            snapshot.products,
            key=lambda p: (
                -(p.backlog_penalty - p.production_cost) / p.unit_capacity,
                p.product_id,
            ),
        )

        for p in ranked:
            max_by_demand = int(p.forecast_demand)
            max_by_capacity = int(remaining // p.unit_capacity)
            qty = max(0, min(max_by_demand, max_by_capacity))
            production[p.product_id] = qty
            remaining -= qty * p.unit_capacity

        backlog = {
            p.product_id: max(p.forecast_demand - production[p.product_id], 0.0)
            for p in snapshot.products
        }
        objective = sum(
            p.production_cost * production[p.product_id]
            + p.backlog_penalty * backlog[p.product_id]
            for p in snapshot.products
        )
        return PlanResult(
            production=production,
            backlog=backlog,
            objective=float(objective),
            planner="greedy_fallback",
            status="Fallback",
        )


class JsonlAuditStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: Mapping) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dict(event), sort_keys=True) + "\n")

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]


@dataclass(frozen=True)
class Decision:
    decision_id: str
    planning_key: str
    input_hash: str
    created_at: str
    result: PlanResult
    used_fallback: bool


class ClosedLoopProductionDecisionSystem:
    def __init__(
        self,
        audit_store: JsonlAuditStore,
        primary_planner: Planner | None = None,
        fallback_planner: Planner | None = None,
        drift_threshold: float = 0.25,
    ) -> None:
        if drift_threshold < 0:
            raise ValueError("drift_threshold must be non-negative")
        self.audit_store = audit_store
        self.primary_planner = primary_planner or MilpProductionPlanner()
        self.fallback_planner = fallback_planner or GreedyFallbackPlanner()
        self.drift_threshold = drift_threshold

    @staticmethod
    def _hash_snapshot(snapshot: ProductionSnapshot) -> str:
        payload = json.dumps(
            snapshot.canonical_payload(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def recommend(self, snapshot: ProductionSnapshot) -> Decision:
        snapshot.validate()
        used_fallback = False
        failure_reason = None

        try:
            result = self.primary_planner.solve(snapshot)
        except Exception as exc:
            used_fallback = True
            failure_reason = f"{type(exc).__name__}: {exc}"
            result = self.fallback_planner.solve(snapshot)

        decision = Decision(
            decision_id=str(uuid4()),
            planning_key=snapshot.planning_key,
            input_hash=self._hash_snapshot(snapshot),
            created_at=datetime.now(timezone.utc).isoformat(),
            result=result,
            used_fallback=used_fallback,
        )

        event = {
            "event_type": "recommendation",
            "decision_id": decision.decision_id,
            "planning_key": decision.planning_key,
            "input_hash": decision.input_hash,
            "created_at": decision.created_at,
            "used_fallback": decision.used_fallback,
            "primary_failure": failure_reason,
            "result": asdict(decision.result),
        }
        self.audit_store.append(event)
        return decision

    def apply_human_override(
        self,
        decision: Decision,
        production_override: Mapping[str, int],
        reason: str,
    ) -> None:
        if not reason.strip():
            raise ValueError("override reason is required")
        unknown = set(production_override) - set(decision.result.production)
        if unknown:
            raise ValueError(f"override contains unknown products: {sorted(unknown)}")
        if any(qty < 0 for qty in production_override.values()):
            raise ValueError("override quantities must be non-negative")

        self.audit_store.append(
            {
                "event_type": "human_override",
                "decision_id": decision.decision_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
                "production_override": dict(production_override),
            }
        )

    def record_execution(
        self,
        decision: Decision,
        forecast_demand: Mapping[str, float],
        actual_demand: Mapping[str, float],
    ) -> dict:
        products = set(decision.result.production)
        if set(forecast_demand) != products or set(actual_demand) != products:
            raise ValueError("forecast and actual demand must match decision products")
        if any(v < 0 for v in forecast_demand.values()) or any(
            v < 0 for v in actual_demand.values()
        ):
            raise ValueError("demand values must be non-negative")

        abs_error = sum(
            abs(float(actual_demand[p]) - float(forecast_demand[p]))
            for p in products
        )
        scale = max(sum(float(forecast_demand[p]) for p in products), 1.0)
        normalized_mae = abs_error / scale
        reoptimize = normalized_mae >= self.drift_threshold

        event = {
            "event_type": "execution_feedback",
            "decision_id": decision.decision_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "normalized_mae": normalized_mae,
            "drift_threshold": self.drift_threshold,
            "reoptimization_required": reoptimize,
            "forecast_demand": dict(forecast_demand),
            "actual_demand": dict(actual_demand),
        }
        self.audit_store.append(event)
        return event


def sample_snapshot() -> ProductionSnapshot:
    return ProductionSnapshot(
        planning_key="plant-a/2026-W40",
        available_capacity=90,
        products=(
            ProductInput("A", 50, 1.0, 3.0, 20.0),
            ProductInput("B", 40, 1.5, 4.0, 15.0),
            ProductInput("C", 30, 2.0, 5.0, 12.0),
        ),
    )


def _demo() -> None:
    system = ClosedLoopProductionDecisionSystem(
        audit_store=JsonlAuditStore("decision_audit.jsonl"),
        drift_threshold=0.20,
    )
    snapshot = sample_snapshot()
    decision = system.recommend(snapshot)
    print("planner:", decision.result.planner)
    print("production:", decision.result.production)
    print("backlog:", decision.result.backlog)

    feedback = system.record_execution(
        decision,
        forecast_demand={p.product_id: p.forecast_demand for p in snapshot.products},
        actual_demand={"A": 65, "B": 38, "C": 36},
    )
    print("reoptimization_required:", feedback["reoptimization_required"])


if __name__ == "__main__":
    _demo()
