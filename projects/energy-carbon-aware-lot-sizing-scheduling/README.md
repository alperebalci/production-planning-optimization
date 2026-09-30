# Energy- and Carbon-Aware Lot Sizing and Scheduling

A multi-period production-planning MILP that combines lot/setup decisions with electricity economics and carbon intensity.

The model jointly decides:

- production quantities and binary setups,
- inventory/backlog,
- grid electricity use,
- battery charging/discharging and state of charge.

Grid energy carries both a tariff and a carbon-price term:

```text
effective grid cost_t
= electricity_price_t
+ carbon_price * carbon_intensity_t
```

Onsite PV enters the energy balance directly. The planner can therefore pre-build inventory in cleaner/cheaper periods when capacity and holding costs justify it.

Natural extensions are multiple products/machines, demand charges, battery efficiency, renewable curtailment, emissions caps, certificates, and detailed shift-level scheduling.
