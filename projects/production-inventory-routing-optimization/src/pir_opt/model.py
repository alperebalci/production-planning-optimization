"""Integrated production, inventory, and route-based distribution MILP."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations

import numpy as np
from numpy.typing import ArrayLike,NDArray
from scipy.optimize import Bounds,LinearConstraint,milp


@dataclass(frozen=True)
class Route:
    customers:tuple[int,...]
    cost:float


def enumerate_routes(coordinates:ArrayLike)->list[Route]:
    pts=np.asarray(coordinates,float)
    n=len(pts)-1
    dist=np.linalg.norm(pts[:,None,:]-pts[None,:,:],axis=2)
    routes=[]
    for k in range(1,n+1):
        for subset in combinations(range(1,n+1),k):
            best=None
            for order in permutations(subset):
                cost=dist[0,order[0]]+sum(dist[order[i],order[i+1]] for i in range(len(order)-1))+dist[order[-1],0]
                if best is None or cost<best[0]:
                    best=(float(cost),tuple(order))
            assert best is not None
            routes.append(Route(best[1],best[0]))
    return routes


@dataclass(frozen=True)
class PIRInstance:
    coordinates:NDArray[np.float64]
    demand:NDArray[np.float64]
    production_capacity:NDArray[np.float64]
    vehicle_capacity:float
    production_cost:float=1.0
    plant_holding:float=0.1
    customer_holding:float=0.2
    route_cost_scale:float=1.0

    @classmethod
    def from_arrays(cls,coordinates:ArrayLike,demand:ArrayLike,production_capacity:ArrayLike,vehicle_capacity:float)->"PIRInstance":
        pts=np.asarray(coordinates,float)
        d=np.asarray(demand,float)
        cap=np.asarray(production_capacity,float)
        if pts.ndim!=2 or pts.shape[1]!=2 or d.ndim!=2 or d.shape[1]!=len(pts)-1 or cap.shape!=(d.shape[0],):
            raise ValueError("dimension mismatch")
        return cls(pts,d,cap,float(vehicle_capacity))


@dataclass(frozen=True)
class PIRResult:
    production:NDArray[np.float64]
    plant_inventory:NDArray[np.float64]
    customer_inventory:NDArray[np.float64]
    route_use:NDArray[np.int64]
    deliveries:NDArray[np.float64]
    routes:tuple[Route,...]
    objective:float


def solve_pir(instance:PIRInstance)->PIRResult:
    routes=enumerate_routes(instance.coordinates)
    T,C=instance.demand.shape
    R=len(routes)
    # variables prod[T], plantinv[T], custinv[T,C], use[T,R], deliv[T,R,C]
    p0=0;pi0=T;ci0=2*T;u0=ci0+T*C;d0=u0+T*R;n=d0+T*R*C
    def ci(t,c): return ci0+t*C+c
    def ui(t,r): return u0+t*R+r
    def di(t,r,c): return d0+(t*R+r)*C+c
    obj=np.zeros(n)
    obj[p0:pi0]=instance.production_cost
    obj[pi0:ci0]=instance.plant_holding
    obj[ci0:u0]=instance.customer_holding
    for t in range(T):
        for r,route in enumerate(routes):
            obj[ui(t,r)]=instance.route_cost_scale*route.cost
    lb=np.zeros(n);ub=np.full(n,np.inf);integ=np.zeros(n,int)
    ub[p0:pi0]=instance.production_capacity
    ub[u0:d0]=1;integ[u0:d0]=1
    rows=[];lows=[];highs=[]
    # plant balance
    for t in range(T):
        row=np.zeros(n);row[pi0+t]=1;row[p0+t]=-1
        if t>0: row[pi0+t-1]-=1
        for r in range(R):
            for c in range(C): row[di(t,r,c)]+=1
        rows.append(row);lows.append(0);highs.append(0)
    # customer inventory balance
    for t in range(T):
        for c in range(C):
            row=np.zeros(n);row[ci(t,c)]=1
            if t>0: row[ci(t-1,c)]-=1
            for r,route in enumerate(routes):
                if c+1 in route.customers: row[di(t,r,c)]-=1
            rows.append(row);lows.append(-instance.demand[t,c]);highs.append(-instance.demand[t,c])
    # route capacity and forbid deliveries to nonmembers
    for t in range(T):
        for r,route in enumerate(routes):
            row=np.zeros(n)
            for c in range(C):
                row[di(t,r,c)]=1
                if c+1 not in route.customers:
                    ub[di(t,r,c)]=0
            row[ui(t,r)]=-instance.vehicle_capacity
            rows.append(row);lows.append(-np.inf);highs.append(0)
    res=milp(c=obj,integrality=integ,bounds=Bounds(lb,ub),constraints=LinearConstraint(np.stack(rows),lows,highs))
    if not res.success or res.x is None:
        raise RuntimeError(res.message)
    x=res.x
    return PIRResult(
        production=x[p0:pi0],
        plant_inventory=x[pi0:ci0],
        customer_inventory=x[ci0:u0].reshape(T,C),
        route_use=np.rint(x[u0:d0]).astype(int).reshape(T,R),
        deliveries=x[d0:].reshape(T,R,C),
        routes=tuple(routes),
        objective=float(res.fun),
    )
