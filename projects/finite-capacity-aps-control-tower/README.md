# Finite-Capacity APS Control Tower

An application-oriented planning layer that treats ERP/Excel files as **data interfaces**, not as the optimization engine.

The current core accepts demand, inventory, routings, finite capacity, overtime limits, and cost parameters. It jointly decides:

- internal production,
- subcontracting,
- inventory/backlog,
- resource overtime.

It then generates planner-readable exception messages for bottlenecks, overtime, subcontracting, and backlog.

The intended architecture is:

```text
ERP / Excel / MES
      ↓
validated planning data
      ↓
finite-capacity optimization
      ↓
production + inventory + overtime + subcontract plan
      ↓
bottleneck / exception report
      ↓
planner review and rolling-horizon execution
```

Sibling research projects in this umbrella provide richer engines for integrated lot-sizing/scheduling, forecast-evolution replanning, production–inventory–routing, and energy/carbon-aware planning. The control tower is the operational integration surface, not a replacement for those formulations.
