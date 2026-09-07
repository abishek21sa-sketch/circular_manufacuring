import pytest
from circular_battery.data.demo import demo_chemistry, demo_periods
from circular_battery.engineering.material_flow import calculate_horizon, pack_mass_kg
from circular_battery.domain.models import PeriodInput

def test_demo_pack_mass_is_400kg():
    assert pack_mass_kg(demo_chemistry()) == pytest.approx(400.0)

def test_all_mass_balances_close():
    for r in calculate_horizon(demo_chemistry(), demo_periods()):
        assert abs(r.manufacturing_balance_error_kg) < 1e-8
        assert abs(r.return_balance_error_kg) < 1e-8
        assert abs(r.recycling_balance_error_kg) < 1e-8
        assert abs(r.inventory_balance_error_kg) < 1e-8

def test_rates_are_physical():
    for r in calculate_horizon(demo_chemistry(), demo_periods()):
        assert 0 <= r.recycled_content_rate <= 1
        assert 0 <= r.recovery_efficiency <= 1
        assert 0 <= r.landfill_diversion_rate <= 1

def test_invalid_pathway_shares_rejected():
    p = PeriodInput(1,100,100,.05,50,.8,.5,.4,.3,.9,0)
    with pytest.raises(ValueError):
        calculate_horizon(demo_chemistry(), [p])
