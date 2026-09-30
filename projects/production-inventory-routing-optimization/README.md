# Production–Inventory–Routing Optimization

A route-based MILP that integrates factory production, plant inventory, customer inventory, and distribution-route activation.

The model jointly decides:

- production by period under finite plant capacity,
- finished-goods inventory at the plant,
- customer replenishment quantities,
- which feasible delivery routes operate in each period.

Routes are enumerated exactly for small customer sets and carry a fixed travel cost plus a vehicle-capacity constraint. This is deliberately an integrated benchmark: a cheap production plan is not automatically attractive if it creates expensive or poorly timed distribution.

Natural extensions are multiple products, heterogeneous fleets, time windows, setup/lot-sizing decisions, customer service levels, and column-generation pricing for larger routing instances.
