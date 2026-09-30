"""Finite-capacity ATP/CTP order promising MILP."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class Order:
    product: int
    quantity: float
    requested_period: int
    priority: float = 1.0


@dataclass(frozen=True)
class PromisingInstance:
    orders: tuple[Order, ...]
    initial_inventory: NDArray[np.float64]
    runtime: NDArray[np.float64]
    capacity: NDArray[np.float64]
    production_cost: NDArray[np.float64]
    holding_cost: NDArray[np.float64]
    late_cost: float = 10.0
    reject_cost: float = 100.0

    @classmethod
    def from_arrays(
        cls,
        orders: list[Order] | tuple[Order, ...],
        initial_inventory: ArrayLike,
        runtime: ArrayLike,
        capacity: ArrayLike,
        production_cost: ArrayLike,
        holding_cost: ArrayLike,
        *,
        late_cost: float = 10.0,
        reject_cost: float = 100.0,
    ) -> "PromisingInstance":
        inv = np.asarray(initial_inventory, dtype=float)
        rt = np.asarray(runtime, dtype=float)
        cap = np.asarray(capacity, dtype=float)
        pc = np.asarray(production_cost, dtype=float)
        hc = np.asarray(holding_cost, dtype=float)
        if inv.ndim != 1 or rt.ndim != 2:
            raise ValueError("invalid inventory/runtime dimensions")
        products, resources = rt.shape
        if inv.shape != (products,) or pc.shape != (products,) or hc.shape != (products,):
            raise ValueError("product dimension mismatch")
        if cap.ndim != 2 or cap.shape[1] != resources:
            raise ValueError("capacity must be periods x resources")
        horizon = cap.shape[0]
        checked = tuple(orders)
        for order in checked:
            if order.product < 0 or order.product >= products:
                raise ValueError("order product index out of range")
            if order.quantity <= 0 or not 0 <= order.requested_period < horizon:
                raise ValueError("invalid order quantity/requested period")
        return cls(checked, inv, rt, cap, pc, hc, float(late_cost), float(reject_cost))


@dataclass(frozen=True)
class PromisingResult:
    production: NDArray[np.float64]
    inventory: NDArray[np.float64]
    promise_period: tuple[int | None, ...]
    rejected: NDArray[np.int64]
    objective: float
    explanations: tuple[str, ...]


def solve_order_promising(
    instance: PromisingInstance,
    *,
    allow_ctp: bool = True,
) -> PromisingResult:
    orders = instance.orders
    O = len(orders)
    P = instance.initial_inventory.size
    T, R = instance.capacity.shape

    p0 = 0
    i0 = T * P
    y0 = 2 * T * P
    r0 = y0 + O * T
    n = r0 + O

    def pidx(t, p):
        return p0 + t * P + p

    def iidx(t, p):
        return i0 + t * P + p

    def yidx(o, t):
        return y0 + o * T + t

    c = np.zeros(n)
    for t in range(T):
        for p in range(P):
            c[pidx(t, p)] = instance.production_cost[p]
            c[iidx(t, p)] = instance.holding_cost[p]
    for o, order in enumerate(orders):
        for t in range(T):
            if t >= order.requested_period:
                lateness = t - order.requested_period
                c[yidx(o, t)] = instance.late_cost * order.priority * lateness
        c[r0 + o] = instance.reject_cost * order.priority

    lb = np.zeros(n)
    ub = np.full(n, np.inf)
    integrality = np.zeros(n, dtype=int)
    if not allow_ctp:
        ub[p0:i0] = 0.0
    ub[y0:r0] = 1.0
    integrality[y0:r0] = 1
    ub[r0:] = 1.0
    integrality[r0:] = 1

    for o, order in enumerate(orders):
        for t in range(order.requested_period):
            ub[yidx(o, t)] = 0.0

    rows = []
    lows = []
    highs = []

    for o in range(O):
        row = np.zeros(n)
        for t in range(T):
            row[yidx(o, t)] = 1.0
        row[r0 + o] = 1.0
        rows.append(row)
        lows.append(1.0)
        highs.append(1.0)

    for t in range(T):
        for r in range(R):
            row = np.zeros(n)
            for p in range(P):
                row[pidx(t, p)] = instance.runtime[p, r]
            rows.append(row)
            lows.append(-np.inf)
            highs.append(instance.capacity[t, r])

    for t in range(T):
        for p in range(P):
            row = np.zeros(n)
            row[iidx(t, p)] = 1.0
            row[pidx(t, p)] = -1.0
            if t > 0:
                row[iidx(t - 1, p)] = -1.0
                rhs = 0.0
            else:
                rhs = instance.initial_inventory[p]
            for o, order in enumerate(orders):
                if order.product == p:
                    row[yidx(o, t)] += order.quantity
            rows.append(row)
            lows.append(rhs)
            highs.append(rhs)

    result = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(lb, ub),
        constraints=LinearConstraint(np.stack(rows), np.asarray(lows), np.asarray(highs)),
        options={"disp": False},
    )
    if not result.success or result.x is None:
        raise RuntimeError(result.message)

    x = result.x
    production = x[p0:i0].reshape(T, P)
    inventory = x[i0:y0].reshape(T, P)
    y = np.rint(x[y0:r0]).astype(int).reshape(O, T)
    rejected = np.rint(x[r0:]).astype(int)

    promised = []
    explanations = []
    for o, order in enumerate(orders):
        if rejected[o]:
            promised.append(None)
            explanations.append(
                f"order {o+1}: rejected; insufficient economical ATP/CTP within horizon"
            )
            continue
        period = int(np.argmax(y[o]))
        promised.append(period)
        if period == order.requested_period:
            source = "ATP/CTP feasible on requested period"
        else:
            source = f"delayed by {period-order.requested_period} period(s) due to supply/capacity"
        explanations.append(f"order {o+1}: promise period {period+1}; {source}")

    return PromisingResult(
        production=production,
        inventory=inventory,
        promise_period=tuple(promised),
        rejected=rejected,
        objective=float(result.fun),
        explanations=tuple(explanations),
    )
