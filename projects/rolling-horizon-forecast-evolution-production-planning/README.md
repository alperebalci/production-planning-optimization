# Rolling-Horizon Forecast-Evolution Production Planning

A finite-capacity replanning benchmark that treats forecast history and plan stability as first-class data.

The model distinguishes:

- **frozen zone** — previously released production quantities cannot change;
- **slushy zone** — changes are allowed but explicitly penalized;
- **liquid zone** — future quantities can move freely.

Every replan minimizes production, inventory, backlog, and plan-change cost. Forecast vintages can be represented explicitly through additive revisions.

This project studies a practical source of planning failure: mathematically cheap replans can be operationally destructive if they repeatedly rewrite near-term production. Natural extensions are scenario-based forecast evolution, service-level constraints, multi-product capacity, and stochastic recourse.
