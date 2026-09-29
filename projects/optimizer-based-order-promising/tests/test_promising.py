from order_promising import Order, PromisingInstance, solve_order_promising


def make_instance():
    return PromisingInstance.from_arrays(
        orders=[
            Order(product=0, quantity=4, requested_period=0, priority=2),
            Order(product=0, quantity=3, requested_period=0, priority=1),
        ],
        initial_inventory=[4],
        runtime=[[1.0]],
        capacity=[[0.0], [3.0], [3.0]],
        production_cost=[1.0],
        holding_cost=[0.1],
        late_cost=5.0,
        reject_cost=100.0,
    )


def test_atp_only_cannot_create_supply():
    result=solve_order_promising(make_instance(),allow_ctp=False)
    assert result.production.sum()==0
    assert result.rejected.sum()>=1


def test_ctp_can_create_supply_and_reduce_rejections():
    atp=solve_order_promising(make_instance(),allow_ctp=False)
    ctp=solve_order_promising(make_instance(),allow_ctp=True)
    assert ctp.production.sum()>0
    assert ctp.rejected.sum()<atp.rejected.sum()


def test_promises_are_not_before_requested_date():
    inst=make_instance()
    result=solve_order_promising(inst,allow_ctp=True)
    for order,period in zip(inst.orders,result.promise_period):
        if period is not None:
            assert period>=order.requested_period
