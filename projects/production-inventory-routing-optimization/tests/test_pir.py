import numpy as np

from pir_opt import PIRInstance,solve_pir


def test_integrated_production_inventory_routing_is_feasible():
    inst=PIRInstance.from_arrays(
        coordinates=[[0,0],[1,0],[0,1]],
        demand=[[2,2],[3,1]],
        production_capacity=[6,6],
        vehicle_capacity=4,
    )
    r=solve_pir(inst)
    assert np.all(r.production<=inst.production_capacity+1e-8)
    for t in range(inst.demand.shape[0]):
        for rid,route in enumerate(r.routes):
            assert r.deliveries[t,rid].sum()<=inst.vehicle_capacity*r.route_use[t,rid]+1e-8
    # cumulative delivered + ending inventory must cover cumulative demand
    delivered=r.deliveries.sum(axis=1)
    assert np.allclose(np.cumsum(delivered,axis=0),np.cumsum(inst.demand,axis=0)+r.customer_inventory,atol=1e-7)
