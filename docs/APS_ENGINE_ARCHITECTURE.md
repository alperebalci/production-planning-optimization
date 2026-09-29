# APS Engine Architecture

This repository is evolving from a set of production-planning examples into an **ERP-independent Advanced Planning & Scheduling (APS) research engine**.

The goal is not to reproduce SAP, Oracle, Kinaxis, o9, or another commercial product. The goal is to make the Operations Research layer behind advanced manufacturing planning explicit, testable, and reproducible.

## System boundary

~~~text
ERP / MES / WMS / Excel
        |
        | orders, forecast, inventory, BOM, routing,
        | resources, calendars, costs, maintenance
        v
+-------------------------------+
| Planning data model           |
| validation + normalization    |
+---------------+---------------+
                |
                v
+-------------------------------+
| Net requirements / pegging    |
| ATP / CTP order promising     |
+---------------+---------------+
                |
                v
+-------------------------------+
| Finite-capacity optimizer     |
| lot sizing                    |
| inventory / backlog           |
| overtime / subcontract        |
+---------------+---------------+
                |
                v
+-------------------------------+
| Detailed scheduling           |
| sequence / setup / campaigns  |
+---------------+---------------+
                |
                v
+-------------------------------+
| Rolling-horizon replanning    |
| frozen / slushy / liquid      |
| nervousness penalties         |
+---------------+---------------+
                |
                v
+-------------------------------+
| Simulation / digital twin     |
| feasibility + stress testing  |
+---------------+---------------+
                |
                v
+-------------------------------+
| Exception / explanation layer|
| bottlenecks, lateness, OT,    |
| subcontract, rejected orders  |
+---------------+---------------+
                |
                v
        planner / execution
~~~

## Research modules

| Module | Decision question |
|---|---|
| multi-level-production-planning-milp | What should be produced under BOM, inventory, lead-time and finite-capacity constraints? |
| integrated-lot-sizing-and-scheduling | Is the aggregate plan still feasible after sequence-dependent setups are represented? |
| rolling-horizon-forecast-evolution-production-planning | How should the plan change when forecasts change without creating excessive nervousness? |
| production-inventory-routing-optimization | How should production and replenishment be coordinated with distribution routes? |
| energy-carbon-aware-lot-sizing-scheduling | When should production move across periods because energy/carbon conditions differ? |
| optimizer-based-order-promising | Can an order be promised from existing supply (ATP) or newly created finite-capacity supply (CTP)? |
| finite-capacity-aps-control-tower | How are optimization decisions exposed as planner-readable exceptions and actions? |

Production/maintenance integration is developed in the sibling manufacturing-systems-optimization umbrella.

## Design principles

1. ERP is a system of record, not the optimization model.
2. Excel can remain an input/output surface, but not the decision algorithm.
3. Finite capacity must be explicit.
4. A production plan should be executable, not merely material-feasible.
5. Replanning must price instability, not only production cost.
6. Human overrides and frozen decisions are legitimate constraints.
7. Every important exception should have an explanation.
8. Exact models and heuristics should be compared under the same data contract.

## Solver strategy

Different planning layers call for different engines:

- LP/MILP: HiGHS, Gurobi, CPLEX;
- scheduling/logic: CP-SAT / CP;
- large decomposition models: Benders / column generation / Lagrangian methods;
- fast replanning: rolling horizon, LNS, problem-specific heuristics;
- uncertainty: stochastic programming / DRO;
- black-box operational validation: simulation optimization / digital twin.

The research objective is not to force one solver onto every planning problem. It is to make the optimization boundary explicit enough that solver choice becomes an engineering decision.
