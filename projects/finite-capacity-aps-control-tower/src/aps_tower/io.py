"""ERP/Excel-like dataframe contract helpers."""

from __future__ import annotations

import pandas as pd


REQUIRED_DEMAND_COLUMNS={"period","product_id","quantity"}
REQUIRED_CAPACITY_COLUMNS={"period","resource_id","capacity_hours"}


def validate_demand_frame(frame:pd.DataFrame)->None:
    missing=REQUIRED_DEMAND_COLUMNS-set(frame.columns)
    if missing:
        raise ValueError(f"missing demand columns: {sorted(missing)}")
    if (frame["quantity"]<0).any():
        raise ValueError("demand quantity must be non-negative")


def validate_capacity_frame(frame:pd.DataFrame)->None:
    missing=REQUIRED_CAPACITY_COLUMNS-set(frame.columns)
    if missing:
        raise ValueError(f"missing capacity columns: {sorted(missing)}")
    if (frame["capacity_hours"]<0).any():
        raise ValueError("capacity must be non-negative")
