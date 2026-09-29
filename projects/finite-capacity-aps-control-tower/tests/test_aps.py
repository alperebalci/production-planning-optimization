import numpy as np
import pandas as pd

from aps_tower import APSInstance,solve_aps,validate_demand_frame


def test_aps_generates_feasible_plan_and_exceptions():
    inst=APSInstance.from_arrays(
        demand=[[5,4],[6,5]],
        initial_inventory=[0,0],
        runtime=[[1,.2],[.5,1]],
        capacity=[[6,6],[6,6]],
        overtime_limit=[[2,2],[2,2]],
        production_cost=[1,1],
        holding_cost=[.1,.1],
        backlog_cost=[50,50],
        subcontract_cost=[10,10],
        overtime_cost=[3,3],
    )
    r=solve_aps(inst)
    assert np.all(r.production@inst.runtime<=inst.capacity+r.overtime+1e-8)
    assert isinstance(r.exceptions,tuple)


def test_excel_like_demand_contract():
    frame=pd.DataFrame({"period":[1],"product_id":["A"],"quantity":[5.]})
    validate_demand_frame(frame)
