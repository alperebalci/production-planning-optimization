# From Manual Production Planning to Optimization Engineering

Production planning can be performed at very different analytical levels even when the job title is identical.

This repository targets the **optimization-engineering** end of that spectrum.

## Coordination-heavy planning

A planner may spend much of the day exporting ERP data, moving quantities between spreadsheets, checking shortages, calling production/purchasing/sales, changing dates after disruptions, and manually prioritizing urgent orders.

Those activities can be operationally important. The analytical limitation is that manual coordination alone does not establish whether the resulting plan is globally feasible, cost-efficient, stable, or capacity-consistent.

## Optimization-oriented planning

The same operational questions can be written as a decision model:

~~~text
orders + forecast + inventory
+ BOM + routing + lead times
+ work-center capacity + shifts
+ setup + lot sizes + maintenance
+ overtime + subcontract + service policy
                |
                v
        mathematical optimizer
                |
                v
production / inventory / promise dates / schedule
                |
                v
bottleneck and exception explanation
~~~

Typical objective terms include inventory, backlog/tardiness, setup/changeover, overtime, subcontracting, transportation, energy/carbon, and plan-instability penalties.

Hard constraints include BOM balance, finite capacity, resource eligibility, calendars, lot sizes, maintenance windows, and frozen orders.

## Professional positioning

The technical profile represented by this repository is closer to:

- Advanced Planning & Scheduling (APS) Optimization Engineer;
- Manufacturing Optimization Specialist;
- Operations Research Specialist — Manufacturing Planning & Scheduling;
- Manufacturing Decision Scientist.

The distinction is not about job-title prestige or educational pedigree. It is about **what decision layer can be designed, modeled, validated, and integrated**.

A strong optimization engineer should be able to:

1. translate ERP/MES data into a mathematical planning model;
2. distinguish material feasibility from capacity feasibility;
3. choose LP/MILP/CP/decomposition/heuristic methods deliberately;
4. quantify trade-offs instead of hiding them in manual overrides;
5. design rolling-horizon policies and frozen zones;
6. explain why an order is late, rejected, subcontracted, or capacity-constrained;
7. integrate the optimizer back into planner and execution workflows;
8. validate the policy against simulation or real operational data.

That is the capability this portfolio is intended to demonstrate.
