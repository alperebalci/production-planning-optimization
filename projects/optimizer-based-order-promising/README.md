# Optimizer-Based Order Promising (ATP / CTP)

A finite-capacity order-promising laboratory for the commercial question:

**Can I promise this customer order, and on which date, without breaking material and resource feasibility?**

The project separates two modes:

- **ATP (Available-to-Promise):** only current inventory is available; the optimizer cannot create new production.
- **CTP (Capable-to-Promise):** the optimizer may create future production subject to finite resource capacity.

For every order the model chooses exactly one promise period or rejects the order. It jointly optimizes production, inventory, finite resource capacity, requested dates, lateness cost, order priority, and rejection cost.

The model therefore does more than subtract sales orders from stock. It asks whether new supply can be manufactured within capacity and whether the resulting promise date is economically sensible.

## Why this belongs in an APS engine

Modern order-promising systems sit between order capture and planning. A robust promise needs visibility into current/planned supply, BOM/routing/resource capacity, and current demand commitments.

Current scope is single-site manufacturing with fixed order quantities and no split shipments. Natural extensions include BOM/component availability, buy/transfer sources, multiple plants, substitutions, allocations/supply protection, transportation lead times, split fulfillment, and concurrent reservation logic.
