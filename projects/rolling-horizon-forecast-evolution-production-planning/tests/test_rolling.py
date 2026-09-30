import numpy as np

from rolling_plan import forecast_revision_path,solve_replan


def test_frozen_zone_is_preserved():
    first=solve_replan([5,5,5,5],[8,8,8,8],frozen_periods=0)
    second=solve_replan(
        [9,2,7,3],[8,8,8,8],first.production,
        frozen_periods=1,slushy_periods=2,change_penalty=5,
    )
    assert np.isclose(second.production[0],first.production[0])


def test_higher_stability_penalty_reduces_slushy_changes():
    prev=np.array([4.,4.,4.,4.])
    low=solve_replan([4,8,1,6],[10]*4,prev,frozen_periods=1,slushy_periods=2,change_penalty=.01)
    high=solve_replan([4,8,1,6],[10]*4,prev,frozen_periods=1,slushy_periods=2,change_penalty=50)
    assert high.changes[1:3].sum()<=low.changes[1:3].sum()+1e-8


def test_forecast_vintages_accumulate_revisions():
    path=forecast_revision_path([10,10],[[1,-1],[2,0]])
    assert np.allclose(path,[[10,10],[11,9],[13,9]])
