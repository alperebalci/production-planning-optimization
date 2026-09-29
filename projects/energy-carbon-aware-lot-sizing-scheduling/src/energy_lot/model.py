"""Energy- and carbon-aware multi-period lot-sizing MILP with storage."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike,NDArray
from scipy.optimize import Bounds,LinearConstraint,milp


@dataclass(frozen=True)
class EnergyLotInstance:
    demand:NDArray[np.float64]
    capacity:NDArray[np.float64]
    electricity_price:NDArray[np.float64]
    carbon_intensity:NDArray[np.float64]
    pv_generation:NDArray[np.float64]
    energy_per_unit:float
    setup_energy:float
    max_lot:float
    battery_capacity:float
    charge_limit:float
    discharge_limit:float
    carbon_price:float
    setup_cost:float=1.0
    holding_cost:float=.2
    backlog_cost:float=30.0

    @classmethod
    def from_arrays(
        cls,
        demand:ArrayLike,
        capacity:ArrayLike,
        electricity_price:ArrayLike,
        carbon_intensity:ArrayLike,
        pv_generation:ArrayLike,
        *,
        energy_per_unit:float=1.0,
        setup_energy:float=.5,
        max_lot:float=20.0,
        battery_capacity:float=5.0,
        charge_limit:float=3.0,
        discharge_limit:float=3.0,
        carbon_price:float=0.0,
    )->"EnergyLotInstance":
        arrays=[np.asarray(v,float) for v in (demand,capacity,electricity_price,carbon_intensity,pv_generation)]
        if arrays[0].ndim!=1 or any(a.shape!=arrays[0].shape for a in arrays[1:]):
            raise ValueError("all time-series inputs must have equal length")
        return cls(*arrays,float(energy_per_unit),float(setup_energy),float(max_lot),
                   float(battery_capacity),float(charge_limit),float(discharge_limit),
                   float(carbon_price))


@dataclass(frozen=True)
class EnergyLotResult:
    production:NDArray[np.float64]
    setup:NDArray[np.int64]
    inventory:NDArray[np.float64]
    backlog:NDArray[np.float64]
    grid:NDArray[np.float64]
    charge:NDArray[np.float64]
    discharge:NDArray[np.float64]
    soc:NDArray[np.float64]
    objective:float


def solve_energy_plan(instance:EnergyLotInstance)->EnergyLotResult:
    T=len(instance.demand)
    # prod, setup, inv, back, grid, charge, discharge, soc
    p0=0;s0=T;i0=2*T;b0=3*T;g0=4*T;c0=5*T;d0=6*T;soc0=7*T;n=8*T
    obj=np.zeros(n)
    obj[s0:i0]=instance.setup_cost
    obj[i0:b0]=instance.holding_cost
    obj[b0:g0]=instance.backlog_cost
    obj[g0:c0]=instance.electricity_price+instance.carbon_price*instance.carbon_intensity
    lb=np.zeros(n);ub=np.full(n,np.inf);integ=np.zeros(n,int)
    ub[p0:s0]=instance.capacity
    ub[s0:i0]=1;integ[s0:i0]=1
    ub[c0:d0]=instance.charge_limit
    ub[d0:soc0]=instance.discharge_limit
    ub[soc0:]=instance.battery_capacity
    rows=[];lows=[];highs=[]
    # lot/setup link and inventory balance
    for t in range(T):
        row=np.zeros(n);row[p0+t]=1;row[s0+t]=-instance.max_lot
        rows.append(row);lows.append(-np.inf);highs.append(0)
        row=np.zeros(n);row[i0+t]=1;row[b0+t]=-1;row[p0+t]=-1
        if t>0:
            row[i0+t-1]-=1;row[b0+t-1]+=1
        rows.append(row);lows.append(-instance.demand[t]);highs.append(-instance.demand[t])
    # energy balance: grid + pv + discharge = process + setup + charge
    for t in range(T):
        row=np.zeros(n)
        row[g0+t]=1;row[d0+t]=1;row[c0+t]-=1
        row[p0+t]-=instance.energy_per_unit
        row[s0+t]-=instance.setup_energy
        rhs=-instance.pv_generation[t]
        rows.append(row);lows.append(rhs);highs.append(rhs)
    # battery SOC
    for t in range(T):
        row=np.zeros(n);row[soc0+t]=1;row[c0+t]-=1;row[d0+t]+=1
        if t>0: row[soc0+t-1]-=1
        rows.append(row);lows.append(0);highs.append(0)
    res=milp(c=obj,integrality=integ,bounds=Bounds(lb,ub),constraints=LinearConstraint(np.stack(rows),lows,highs))
    if not res.success or res.x is None:
        raise RuntimeError(res.message)
    x=res.x
    return EnergyLotResult(
        x[p0:s0],np.rint(x[s0:i0]).astype(int),x[i0:b0],x[b0:g0],
        x[g0:c0],x[c0:d0],x[d0:soc0],x[soc0:],float(res.fun)
    )
