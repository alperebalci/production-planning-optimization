# ERP-to-Optimization Data Contract

An APS engine is only as good as the data contract connecting it to ERP/MES systems.

The optimization layer should not depend on a specific vendor schema. SAP, Oracle, Dynamics, custom ERP, CSV, or Excel exports should map into the same canonical entities.

## Core entities

### Products and materials
- product/material id
- make/buy type
- lead time
- lot-size rules
- holding/backlog/service costs
- unit conversions

### BOM
- parent product
- component
- quantity per parent
- effective dates / versions

### Routing / recipe
- product
- operation
- eligible resource/work center
- runtime per unit
- fixed setup time
- sequence-dependent setup family where relevant

### Resources
- resource/work center
- shift/calendar capacity
- overtime limits
- planned downtime / maintenance
- efficiency factors

### Demand
- sales order / forecast id
- product
- requested date
- quantity
- priority / customer class
- firm vs forecast status

### Supply and inventory
- on-hand inventory
- work orders / planned orders
- purchase orders
- transfer orders
- scheduled receipts
- safety stock / reservation status

### Execution feedback
- actual production
- actual yield/scrap
- actual downtime
- actual setup duration
- order completion timestamps

## Data quality checks

Before optimization, validate:

- duplicated identifiers;
- missing routing/BOM links;
- inconsistent units;
- negative or impossible capacities;
- overlapping calendars;
- demand outside the planning horizon;
- cyclic BOMs;
- orders assigned to products with no feasible resource;
- stale master-data versions.

The optimizer should fail loudly on structural data defects rather than silently producing a plan from inconsistent input.

## Vendor boundary

ERP remains authoritative for transactional state. The optimization service consumes a snapshot, computes decisions, and returns proposed planned orders, dates, quantities, allocations, promise dates, and exception reasons.

This separation keeps the OR layer testable and portable across ERP systems.
