"""Rolling-horizon finite-capacity planning with forecast evolution and plan stability."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike,NDArray
from scipy.optimize import Bounds,LinearConstraint,milp


@dataclass(frozen=True)
class RollingPlanResult:
    production:NDArray[np.float64]
    inventory:NDArray[np.float64]
    backlog:NDArray[np.float64]
    changes:NDArray[np.float64]
    objective:float


def solve_replan(
    forecast:ArrayLike,
    capacity:ArrayLike,
    previous_plan:ArrayLike|None=None,
    *,
    initial_inventory:float=0.0,
    frozen_periods:int=1,
    slushy_periods:int=2,
    production_cost:float=1.0,
    holding_cost:float=0.2,
    backlog_cost:float=20.0,
    change_penalty:float=2.0,
)->RollingPlanResult:
    d=np.asarray(forecast,float)
    cap=np.asarray(capacity,float)
    if d.ndim!=1 or cap.shape!=d.shape:
        raise ValueError("forecast and capacity must be same-length vectors")
    T=len(d)
    prev=np.zeros(T) if previous_plan is None else np.asarray(previous_plan,float)
    if prev.shape!=(T,):
        raise ValueError("previous_plan must match horizon")
    n=5*T
    x0=0;i0=T;b0=2*T;dp0=3*T;dm0=4*T
    c=np.zeros(n)
    c[x0:i0]=production_cost
    c[i0:b0]=holding_cost
    c[b0:dp0]=backlog_cost
    for t in range(min(T,frozen_periods+slushy_periods)):
        c[dp0+t]=change_penalty
        c[dm0+t]=change_penalty
    lb=np.zeros(n);ub=np.full(n,np.inf)
    ub[x0:i0]=cap
    rows=[];lows=[];highs=[]
    # inventory-backlog balance
    for t in range(T):
        row=np.zeros(n)
        row[i0+t]=1;row[b0+t]=-1;row[x0+t]=-1
        if t>0:
            row[i0+t-1]-=1;row[b0+t-1]+=1
            rhs=-d[t]
        else:
            rhs=initial_inventory-d[t]
        rows.append(row);lows.append(rhs);highs.append(rhs)
    # absolute plan changes x-prev = dplus-dminus
    for t in range(T):
        row=np.zeros(n)
        row[x0+t]=1;row[dp0+t]=-1;row[dm0+t]=1
        rows.append(row);lows.append(prev[t]);highs.append(prev[t])
    # frozen zone
    if previous_plan is not None:
        for t in range(min(frozen_periods,T)):
            row=np.zeros(n);row[x0+t]=1
            rows.append(row);lows.append(prev[t]);highs.append(prev[t])
    res=milp(c=c,bounds=Bounds(lb,ub),constraints=LinearConstraint(np.stack(rows),lows,highs))
    if not res.success or res.x is None:
        raise RuntimeError(res.message)
    x=res.x
    return RollingPlanResult(
        production=x[x0:i0],
        inventory=x[i0:b0],
        backlog=x[b0:dp0],
        changes=x[dp0:dm0]+x[dm0:],
        objective=float(res.fun),
    )


def forecast_revision_path(
    initial:ArrayLike,
    revisions:ArrayLike,
)->NDArray[np.float64]:
    """Build forecast vintages from an initial forecast and additive revision rows."""
    base=np.asarray(initial,float)
    rev=np.asarray(revisions,float)
    if rev.ndim!=2 or rev.shape[1]!=base.size:
        raise ValueError("revisions must be vintages x horizon")
    return np.vstack([base,base+np.cumsum(rev,axis=0)])
