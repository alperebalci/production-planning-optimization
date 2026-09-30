"""Finite-capacity APS planning core and planner-readable exception reporting."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike,NDArray
from scipy.optimize import Bounds,LinearConstraint,milp


@dataclass(frozen=True)
class APSInstance:
    demand:NDArray[np.float64]
    initial_inventory:NDArray[np.float64]
    runtime:NDArray[np.float64]
    capacity:NDArray[np.float64]
    overtime_limit:NDArray[np.float64]
    production_cost:NDArray[np.float64]
    holding_cost:NDArray[np.float64]
    backlog_cost:NDArray[np.float64]
    subcontract_cost:NDArray[np.float64]
    overtime_cost:NDArray[np.float64]

    @classmethod
    def from_arrays(
        cls,
        demand:ArrayLike,
        initial_inventory:ArrayLike,
        runtime:ArrayLike,
        capacity:ArrayLike,
        overtime_limit:ArrayLike,
        *,
        production_cost:ArrayLike,
        holding_cost:ArrayLike,
        backlog_cost:ArrayLike,
        subcontract_cost:ArrayLike,
        overtime_cost:ArrayLike,
    )->"APSInstance":
        d=np.asarray(demand,float)
        inv=np.asarray(initial_inventory,float)
        rt=np.asarray(runtime,float)
        cap=np.asarray(capacity,float)
        ot=np.asarray(overtime_limit,float)
        pc=np.asarray(production_cost,float)
        hc=np.asarray(holding_cost,float)
        bc=np.asarray(backlog_cost,float)
        sc=np.asarray(subcontract_cost,float)
        oc=np.asarray(overtime_cost,float)
        if d.ndim!=2:
            raise ValueError("demand must be periods x products")
        T,P=d.shape
        if inv.shape!=(P,) or rt.ndim!=2 or rt.shape[0]!=P:
            raise ValueError("inventory/runtime dimensions invalid")
        R=rt.shape[1]
        if cap.shape!=(T,R) or ot.shape!=(T,R):
            raise ValueError("capacity/overtime must be periods x resources")
        if any(a.shape!=(P,) for a in (pc,hc,bc,sc)) or oc.shape!=(R,):
            raise ValueError("cost dimensions invalid")
        return cls(d,inv,rt,cap,ot,pc,hc,bc,sc,oc)


@dataclass(frozen=True)
class APSResult:
    production:NDArray[np.float64]
    subcontract:NDArray[np.float64]
    inventory:NDArray[np.float64]
    backlog:NDArray[np.float64]
    overtime:NDArray[np.float64]
    utilization:NDArray[np.float64]
    objective:float
    exceptions:tuple[str,...]


def solve_aps(instance:APSInstance)->APSResult:
    T,P=instance.demand.shape;R=instance.runtime.shape[1]
    # prod TP, sub TP, inv TP, back TP, overtime TR
    p0=0;s0=T*P;i0=2*T*P;b0=3*T*P;o0=4*T*P;n=o0+T*R
    def ix(base,t,p): return base+t*P+p
    def ox(t,r): return o0+t*R+r
    c=np.zeros(n)
    for t in range(T):
        for p in range(P):
            c[ix(p0,t,p)]=instance.production_cost[p]
            c[ix(s0,t,p)]=instance.subcontract_cost[p]
            c[ix(i0,t,p)]=instance.holding_cost[p]
            c[ix(b0,t,p)]=instance.backlog_cost[p]
        for r in range(R):
            c[ox(t,r)]=instance.overtime_cost[r]
    lb=np.zeros(n);ub=np.full(n,np.inf)
    for t in range(T):
        for r in range(R):
            ub[ox(t,r)]=instance.overtime_limit[t,r]
    rows=[];lows=[];highs=[]
    # capacity
    for t in range(T):
        for r in range(R):
            row=np.zeros(n)
            for p in range(P): row[ix(p0,t,p)]=instance.runtime[p,r]
            row[ox(t,r)]=-1
            rows.append(row);lows.append(-np.inf);highs.append(instance.capacity[t,r])
    # inventory/backlog balance
    for t in range(T):
        for p in range(P):
            row=np.zeros(n)
            row[ix(i0,t,p)]=1;row[ix(b0,t,p)]=-1
            row[ix(p0,t,p)]-=1;row[ix(s0,t,p)]-=1
            if t>0:
                row[ix(i0,t-1,p)]-=1;row[ix(b0,t-1,p)]+=1
                rhs=-instance.demand[t,p]
            else:
                rhs=instance.initial_inventory[p]-instance.demand[t,p]
            rows.append(row);lows.append(rhs);highs.append(rhs)
    res=milp(c=c,bounds=Bounds(lb,ub),constraints=LinearConstraint(np.stack(rows),lows,highs))
    if not res.success or res.x is None:
        raise RuntimeError(res.message)
    x=res.x
    prod=x[p0:s0].reshape(T,P)
    sub=x[s0:i0].reshape(T,P)
    inv=x[i0:b0].reshape(T,P)
    back=x[b0:o0].reshape(T,P)
    overtime=x[o0:].reshape(T,R)
    load=prod@instance.runtime
    denom=instance.capacity+overtime
    util=np.divide(load,denom,out=np.zeros_like(load),where=denom>1e-12)
    exceptions=[]
    for t in range(T):
        for r in range(R):
            if util[t,r]>=.9:
                exceptions.append(f"period {t+1}: resource {r+1} bottleneck utilization={util[t,r]:.1%}")
            if overtime[t,r]>1e-8:
                exceptions.append(f"period {t+1}: resource {r+1} overtime={overtime[t,r]:.2f}h")
        for p in range(P):
            if back[t,p]>1e-8:
                exceptions.append(f"period {t+1}: product {p+1} backlog={back[t,p]:.2f}")
            if sub[t,p]>1e-8:
                exceptions.append(f"period {t+1}: product {p+1} subcontract={sub[t,p]:.2f}")
    return APSResult(prod,sub,inv,back,overtime,util,float(res.fun),tuple(exceptions))
