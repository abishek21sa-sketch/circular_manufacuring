import pytest
from circular_battery.optimization.critical_materials import demo_critical_material_config, solve_critical_material_plan


def test_critical_material_plan_is_balanced_and_feasible():
    s=solve_critical_material_plan()
    assert s.status=='OPTIMAL'
    assert s.max_constraint_violation < 1e-7
    assert s.total_shortage_kg == pytest.approx(0,abs=1e-7)
    assert 0 < s.recovered_share < 1


def test_critical_material_supplier_concentration_is_bounded():
    cfg=demo_critical_material_config();sol=solve_critical_material_plan(cfg)
    by={m.name:m for m in cfg.materials}
    for row in sol.material_rows:
        q=list(row['virgin_by_supplier_kg'].values());tot=sum(q)
        if tot>1e-9:
            assert max(q)/tot <= by[row['material']].max_single_supplier_share+1e-7


def test_critical_material_hhi_is_physical():
    sol=solve_critical_material_plan()
    assert set(sol.supplier_hhi_by_material)=={'lithium','nickel','cobalt','graphite'}
    assert all(1/3-1e-6 <= x <= 1 for x in sol.supplier_hhi_by_material.values())
