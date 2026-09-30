import numpy as np

from integrated_lss import LSSInstance,solve_integrated


def test_integrated_plan_respects_capacity_and_balance():
    inst=LSSInstance.from_arrays(
        demand=[[4,2],[2,4]],
        capacity=[9,9],
        runtime=[1,1],
        prod_cost=[1,1.1],
        holding_cost=[.2,.2],
        backlog_cost=[20,20],
        changeover=[[0,2],[2,0]],
        slots=2,
        max_lot=6,
    )
    r=solve_integrated(inst)
    assert r.quantity.shape==(2,2,2)
    assert np.all(r.backlog<1e-7)
    for t in range(2):
        assert np.sum(r.assignment[t],axis=1).max()<=1
        runtime=float(np.sum(r.quantity[t]))
        changes=0.0
        if r.assignment[t,0].sum() and r.assignment[t,1].sum():
            p=int(np.argmax(r.assignment[t,0])); q=int(np.argmax(r.assignment[t,1]))
            changes=inst.changeover[p,q]
        assert runtime+changes<=inst.capacity[t]+1e-7
