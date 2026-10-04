# Closed-Loop Production Decision System

This project adds a production-engineering layer around prescriptive analytics. The objective is not to introduce another production-planning formulation; it is to show how an optimizer becomes part of an auditable decision workflow.

The reference flow is:

```text
validated inputs
    -> primary MILP
    -> recommendation
    -> fallback if the optimizer fails
    -> audit log
    -> optional human override
    -> execution feedback
    -> drift check
    -> reoptimization trigger
```

## Why this project exists

An optimization model alone is not a production decision system. Operational deployment also needs explicit input contracts, failure behavior, traceability, override governance, feedback, and a rule for when the decision should be recomputed.

This project demonstrates those controls in a compact form.

## Components

### Data contract

`ProductionSnapshot` validates:

- unique product identifiers;
- non-negative forecast demand;
- positive unit-capacity consumption;
- non-negative costs and penalties;
- non-negative available capacity;
- a non-empty planning key.

Each valid snapshot is serialized deterministically and hashed. The input hash is stored with the recommendation so a decision can be tied back to the exact planning state that produced it.

### Primary optimization path

`MilpProductionPlanner` solves a small integer production-allocation model with PuLP/CBC.

Decision variables:

```text
production_p >= 0, integer
backlog_p >= 0
```

Objective:

```text
minimize
sum_p production_cost_p * production_p
+ backlog_penalty_p * backlog_p
```

Subject to:

```text
sum_p unit_capacity_p * production_p <= available_capacity
production_p + backlog_p >= forecast_demand_p
```

The planner has an explicit solver time limit and validates solver status.

### Deterministic fallback

If the primary planner raises an exception or returns an unacceptable status, `GreedyFallbackPlanner` allocates capacity by avoided backlog penalty per unit of capacity.

The fallback is intentionally simple and deterministic. It is not presented as optimal; its purpose is graceful degradation.

### Audit trail

`JsonlAuditStore` records recommendation, human-override, and execution-feedback events.

Recommendation records include:

- decision ID;
- planning key;
- input hash;
- timestamp;
- planner and solver status;
- objective;
- production and backlog decisions;
- whether a fallback was used;
- primary failure reason when relevant.

### Human override

Overrides require a non-empty reason and are written as separate audit events rather than silently replacing the optimizer output.

This preserves the distinction between:

```text
model recommendation
```

and

```text
executed human-adjusted decision
```

### Execution feedback and reoptimization

`record_execution` compares forecast demand with actual demand using normalized absolute error.

```text
normalized_MAE =
sum |actual_p - forecast_p|
/
max(sum forecast_p, 1)
```

When the metric exceeds the configured threshold, the event marks:

```text
reoptimization_required = true
```

The metric is deliberately simple so the operational control flow remains visible. A production deployment should choose drift and decision-quality metrics that reflect the actual business process.

## Run

From this project directory:

```bash
python decision_system.py
```

This writes example audit events to:

```text
decision_audit.jsonl
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Dependencies

- PuLP

The parent repository already uses PuLP for its production-planning models.

## What this demonstrates

This project explicitly covers the transition:

```text
optimization model
-> prescriptive recommendation
-> governed decision service
-> observed outcome
-> reoptimization
```

That transition is the main difference between a solver demo and a deployable prescriptive-analytics workflow.

## Production limitations

This is a reference architecture, not an APS, MES, or ERP service. A real system would normally add:

- persistent transactional storage rather than local JSONL;
- authenticated APIs;
- schema/version migration;
- idempotency and retry handling;
- concurrent request control;
- solver observability and queueing;
- richer infeasibility diagnosis;
- feature/forecast lineage;
- real execution acknowledgements from MES/ERP;
- decision-quality monitoring, not only forecast drift;
- rollback and shadow-deployment procedures;
- access control around human overrides.

Those concerns are intentionally listed because they are part of prescriptive-analytics engineering even when they are outside the mathematical formulation.
