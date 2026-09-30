import numpy as np

from energy_lot import EnergyLotInstance,solve_energy_plan


def test_energy_balance_and_battery_bounds():
    inst=EnergyLotInstance.from_arrays(
        demand=[0,6,0],
        capacity=[8,8,8],
        electricity_price=[1,4,1],
        carbon_intensity=[1,1,1],
        pv_generation=[2,0,0],
        battery_capacity=4,
        carbon_price=0,
    )
    r=solve_energy_plan(inst)
    assert np.all(r.soc>=-1e-8)
    assert np.all(r.soc<=inst.battery_capacity+1e-8)
    assert np.all(r.backlog<1e-7)


def test_high_carbon_price_discourages_dirty_period_production():
    base=dict(
        demand=[0,5],
        capacity=[6,6],
        electricity_price=[1,1],
        carbon_intensity=[.1,5.0],
        pv_generation=[0,0],
        battery_capacity=0,
        charge_limit=0,
        discharge_limit=0,
    )
    low=solve_energy_plan(EnergyLotInstance.from_arrays(**base,carbon_price=0))
    high=solve_energy_plan(EnergyLotInstance.from_arrays(**base,carbon_price=10))
    assert high.production[0]>=low.production[0]-1e-8
