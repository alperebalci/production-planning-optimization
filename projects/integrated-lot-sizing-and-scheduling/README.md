# Integrated Lot Sizing and Scheduling

A finite-capacity MILP that combines multi-period lot sizing with within-period production sequencing.

Each planning period contains ordered production slots. The model jointly decides:

- production quantity by product and slot,
- slot/product assignment,
- inventory and backlog across periods,
- sequence-dependent changeovers between adjacent slots.

This closes the common planning/scheduling disconnect: a plan is not accepted merely because aggregate period capacity is feasible; changeover time/cost is represented in the same optimization model.

The implementation uses SciPy/HiGHS and is intentionally small enough for exact CI validation. Natural extensions are multiple machines, campaign constraints, family setups, minimum run lengths, detailed calendars, and decomposition.
