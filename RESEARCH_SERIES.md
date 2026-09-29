# Production Planning and Manufacturing Optimization Research Series

This file maps production/manufacturing repositories across planning, scheduling, adaptive control, heuristics, reinforcement learning, and digital-twin workflows. It is an index only: each repository remains independent.

## Production planning and allocation

- `multi-level-production-planning-milp` — multi-level BOM, inventory, backlog, finite capacity, lead times, setups, lot sizes, ATP, and pegging in a deterministic MILP planning model.
- `multi-product-demand-allocation-milp` — multi-product demand/capacity allocation.
- `white-goods-oven-allocation-optimization-milp` — application-specific production/resource allocation.
- `multi-period-warehouse-rental-lp-optimization` — time-phased capacity/rental planning closely related to production/logistics planning.
- `predict-then-optimize-production-planning-spo-plus-pytorch` — contextual production planning with decision-focused learning and SPO+.

## Modern integrated production planning

- `integrated-lot-sizing-and-scheduling` — lot quantities, slot assignments, sequence-dependent changeovers, inventory, and backlog in one MILP.
- `rolling-horizon-forecast-evolution-production-planning` — forecast vintages plus frozen/slushy/liquid zones and explicit plan-nervousness cost.
- `production-inventory-routing-optimization` — plant production, plant/customer inventory, route activation, and vehicle-capacity decisions in one model.
- `energy-carbon-aware-lot-sizing-scheduling` — production setups, inventory, grid electricity, PV, battery storage, and carbon-aware time shifting.
- `finite-capacity-aps-control-tower` — ERP/Excel-facing finite-capacity planning and planner-readable bottleneck/exception reporting.
- `optimizer-based-order-promising` — ATP/CTP promise-date optimization using current inventory and optional finite-capacity future production.

## Classical production scheduling

- `parallel-machine-scheduling-milp-optimization` — exact MILP scheduling on parallel machines.
- `assembly-line-balancing-optimizer-salbp` — assembly-line balancing rather than machine scheduling.
- `resource-constrained-project-scheduling-pulp` — resource-constrained scheduling in project form.
- `optimal-conference-meeting-scheduling-cp-sat` — CP-SAT scheduling in a different application domain; useful as a global-constraint comparison.
- `logic-based-benders-production-scheduling-python` — decomposition-based production scheduling.

## Heuristic and metaheuristic scheduling

- `paint-shop-scheduling-genetic-algorithm` — genetic-algorithm scheduling in an automotive paint-shop setting.
- `flexible-manufacturing-scheduling-genetic-algorithm` — GA for flexible manufacturing scheduling.
- `energy-aware-production-scheduling-ga-java` — energy-aware production scheduling with a genetic algorithm.
- `adaptive-production-scheduling-python` — disruption-aware, forecast-informed heuristic scheduling under changing machine availability.

## Reinforcement learning and dynamic scheduling

- `dynamic-automotive-paint-shop-scheduling-rl` — dynamic paint-shop scheduling with reinforcement learning.
- `job-shop-scheduling-ppo` — PPO scheduling benchmark.
- `reinforcement-learning-job-shop-scheduling-pytorch` — from-scratch Transformer PPO with exact-oracle evaluation.
- `dqn-job-shop-scheduling` — DQN scheduling benchmark.
- `offline-rl-flexible-job-shop-scheduling` — offline RL for flexible job-shop scheduling.
- `safe-rl-constrained-production-control` — constrained/safe RL for production control.
- `production-control-with-mpc-vs-rl` — MPC versus RL for dynamic production control.

## Learning-assisted and neural improvement methods

- `fjsp-ml-rescheduling` — ML-assisted rescheduling in a flexible job-shop context.
- `learning-augmented-online-machine-scheduling-python` — prediction-assisted online scheduling.
- `neural-large-neighborhood-search-job-shop-scheduling-pytorch` — learned neighborhood search for scheduling.

## Simulation and digital-twin bridge

- `manufacturing-discrete-event-simulation-optimization-python` — discrete-event simulation plus optimization.
- `industrial-digital-twin-system-optimization-python` — optimization around an industrial digital-twin workflow.
- `dynamic-manufacturing-digital-twin-rl` — dynamic RL control in a digital-twin setting.
- `manufacturing-lead-time-batch-inference-lightgbm-github-actions` — predictive manufacturing analytics that can feed downstream planning/rescheduling decisions.

## Portfolio rule

Manufacturing is an application domain, not a merge criterion. The portfolio deliberately preserves distinct decision layers:

`planning -> scheduling -> rescheduling -> sequential control -> simulation/digital twin`.

Repositories should remain separate whenever the mathematical formulation, information pattern, or solution paradigm changes materially.
