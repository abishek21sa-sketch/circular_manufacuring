from circular_battery.data.demo import demo_materials, demo_chemistry
from circular_battery.engineering.lca import material_weighted_factor, calculate_lca

def test_recycled_factor_lower_than_virgin_demo_factor():
    c, m = demo_chemistry(), demo_materials()
    assert material_weighted_factor(c,m,True) < material_weighted_factor(c,m,False)

def test_lca_is_additive_and_positive():
    c,m = demo_chemistry(), demo_materials()
    r = calculate_lca(c,m,1000,500,700)
    expected = r.virgin_material_kgco2e+r.recovered_material_kgco2e+r.collection_transport_kgco2e+r.recycling_process_kgco2e
    assert r.total_kgco2e == expected
    assert r.total_kgco2e > 0
