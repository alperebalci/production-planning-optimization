"""Integrated multi-period lot sizing and slot-based sequence scheduling MILP."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class LSSInstance:
    demand: NDArray[np.float64]
    capacity: NDArray[np.float64]
    runtime: NDArray[np.float64]
    prod_cost: NDArray[np.float64]
    holding_cost: NDArray[np.float64]
    backlog_cost: NDArray[np.float64]
    changeover: NDArray[np.float64]
    slots: int
    max_lot: float

    @classmethod
    def from_arrays(
        cls,
        demand: ArrayLike,
        capacity: ArrayLike,
        runtime: ArrayLike,
        prod_cost: ArrayLike,
        holding_cost: ArrayLike,
        backlog_cost: ArrayLike,
        changeover: ArrayLike,
        *,
        slots: int = 2,
        max_lot: float = 100.0,
    ) -> "LSSInstance":
        d=np.asarray(demand,float)
        cap=np.asarray(capacity,float)
        rt=np.asarray(runtime,float)
        pc=np.asarray(prod_cost,float)
        hc=np.asarray(holding_cost,float)
        bc=np.asarray(backlog_cost,float)
        co=np.asarray(changeover,float)
        if d.ndim!=2:
            raise ValueError("demand must be periods x products")
        t,p=d.shape
        if cap.shape!=(t,) or rt.shape!=(p,) or pc.shape!=(p,) or hc.shape!=(p,) or bc.shape!=(p,):
            raise ValueError("dimension mismatch")
        if co.shape!=(p,p):
            raise ValueError("changeover must be products x products")
        if slots<1 or max_lot<=0:
            raise ValueError("invalid slots/max_lot")
        return cls(d,cap,rt,pc,hc,bc,co,int(slots),float(max_lot))


@dataclass(frozen=True)
class LSSResult:
    quantity: NDArray[np.float64]
    assignment: NDArray[np.int64]
    inventory: NDArray[np.float64]
    backlog: NDArray[np.float64]
    objective: float


def solve_integrated(instance:LSSInstance)->LSSResult:
    T,P=instance.demand.shape
    S=instance.slots
    nq=T*S*P
    ny=nq
    ni=T*P
    nb=T*P
    nz=T*max(S-1,0)*P*P
    q0=0
    y0=q0+nq
    i0=y0+ny
    b0=i0+ni
    z0=b0+nb
    n=z0+nz

    def qidx(t,s,p): return q0+(t*S+s)*P+p
    def yidx(t,s,p): return y0+(t*S+s)*P+p
    def iidx(t,p): return i0+t*P+p
    def bidx(t,p): return b0+t*P+p
    def zidx(t,s,p,r): return z0+(((t*(S-1)+(s-1))*P+p)*P+r)

    c=np.zeros(n)
    for t in range(T):
        for s in range(S):
            for p in range(P):
                c[qidx(t,s,p)]=instance.prod_cost[p]
        for p in range(P):
            c[iidx(t,p)]=instance.holding_cost[p]
            c[bidx(t,p)]=instance.backlog_cost[p]
        for s in range(1,S):
            for p in range(P):
                for r in range(P):
                    c[zidx(t,s,p,r)]=instance.changeover[p,r]

    lb=np.zeros(n); ub=np.full(n,np.inf); integ=np.zeros(n,int)
    ub[y0:y0+ny]=1; integ[y0:y0+ny]=1
    if nz:
        ub[z0:]=1; integ[z0:]=1

    rows=[]; lows=[]; highs=[]
    # one product per slot and no gaps
    for t in range(T):
        for s in range(S):
            row=np.zeros(n)
            for p in range(P): row[yidx(t,s,p)]=1
            rows.append(row); lows.append(-np.inf); highs.append(1)
        for s in range(S-1):
            row=np.zeros(n)
            for p in range(P):
                row[yidx(t,s+1,p)]+=1
                row[yidx(t,s,p)]-=1
            rows.append(row); lows.append(-np.inf); highs.append(0)

    # quantity-assignment links and period capacity
    for t in range(T):
        caprow=np.zeros(n)
        for s in range(S):
            for p in range(P):
                row=np.zeros(n); row[qidx(t,s,p)]=1; row[yidx(t,s,p)]=-instance.max_lot
                rows.append(row); lows.append(-np.inf); highs.append(0)
                caprow[qidx(t,s,p)]=instance.runtime[p]
        for s in range(1,S):
            for p in range(P):
                for r in range(P):
                    zij=zidx(t,s,p,r)
                    # z >= y_prev + y_curr - 1
                    row=np.zeros(n); row[zij]=-1; row[yidx(t,s-1,p)]=1; row[yidx(t,s,r)]=1
                    rows.append(row); lows.append(-np.inf); highs.append(1)
                    # z <= each assignment
                    row=np.zeros(n); row[zij]=1; row[yidx(t,s-1,p)]=-1
                    rows.append(row); lows.append(-np.inf); highs.append(0)
                    row=np.zeros(n); row[zij]=1; row[yidx(t,s,r)]=-1
                    rows.append(row); lows.append(-np.inf); highs.append(0)
                    caprow[zij]=instance.changeover[p,r]
        rows.append(caprow); lows.append(-np.inf); highs.append(instance.capacity[t])

    # net inventory balance inv - backlog
    for t in range(T):
        for p in range(P):
            row=np.zeros(n)
            row[iidx(t,p)]=1; row[bidx(t,p)]=-1
            if t>0:
                row[iidx(t-1,p)]-=1; row[bidx(t-1,p)]+=1
            for s in range(S): row[qidx(t,s,p)]-=1
            rows.append(row); lows.append(-instance.demand[t,p]); highs.append(-instance.demand[t,p])

    res=milp(
        c=c,
        integrality=integ,
        bounds=Bounds(lb,ub),
        constraints=LinearConstraint(np.stack(rows),np.asarray(lows),np.asarray(highs)),
        options={"disp":False},
    )
    if not res.success or res.x is None:
        raise RuntimeError(res.message)
    x=res.x
    q=np.array([x[qidx(t,s,p)] for t in range(T) for s in range(S) for p in range(P)]).reshape(T,S,P)
    y=np.rint([x[yidx(t,s,p)] for t in range(T) for s in range(S) for p in range(P)]).astype(int).reshape(T,S,P)
    inv=np.array([x[iidx(t,p)] for t in range(T) for p in range(P)]).reshape(T,P)
    back=np.array([x[bidx(t,p)] for t in range(T) for p in range(P)]).reshape(T,P)
    return LSSResult(q,y,inv,back,float(res.fun))
