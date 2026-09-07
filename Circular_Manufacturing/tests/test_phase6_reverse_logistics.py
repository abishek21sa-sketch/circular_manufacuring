import pytest
from circular_battery.logistics.demo import demo_reverse_logistics_scenario
from circular_battery.logistics.optimizer import solve_reverse_logistics
from circular_battery.logistics.models import CollectionNode,FacilityCandidate,ReverseLogisticsScenario

def test_phase6_reference_network_is_optimal_and_balanced():
    s=demo_reverse_logistics_scenario();sol=solve_reverse_logistics(s)
    assert sol.status=="OPTIMAL"
    assert sol.max_constraint_violation < 1e-6
    assert sol.processed_kg+sol.disposed_kg == pytest.approx(sol.collected_kg,abs=1e-6)
    assert sol.disposed_kg <= sol.collected_kg*s.max_disposal_share+1e-6

def test_phase6_facility_capacities_and_binary_opening():
    s=demo_reverse_logistics_scenario();sol=solve_reverse_logistics(s)
    fac={f.name:f for f in s.facilities}
    used={name:0.0 for name in fac}
    for row in sol.flows: used[row["facility"]]+=row["kg"]
    for name,q in used.items():
        assert q <= fac[name].capacity_kg*sol.opened_facilities[name]+1e-5
        assert sol.opened_facilities[name] in (0,1)

def test_phase6_flow_pathways_match_facility_kind():
    s=demo_reverse_logistics_scenario();sol=solve_reverse_logistics(s)
    kinds={f.name:f.kind for f in s.facilities}
    assert all(row["pathway"]==kinds[row["facility"]] for row in sol.flows)

def test_phase6_transport_impacts_positive_for_nonzero_distance():
    sol=solve_reverse_logistics(demo_reverse_logistics_scenario())
    assert sol.transport_cost > 0
    assert sol.transport_kgco2e > 0
    assert sol.total_kgco2e >= sol.transport_kgco2e

def test_phase6_tiny_oracle_case():
    col=CollectionNode("C",1000,.0,0,0)
    fac=FacilityCandidate("R","recycle",1000,100,2.0,1.0,3,4) # 5 km
    s=ReverseLogisticsScenario(
        collections=(col,),facilities=(fac,),collection_rate=1.0,
        transport_cost_per_kg_km=.01,transport_kgco2e_per_kg_km=.001,
        disposal_cost_per_kg=99,max_disposal_share=0.0
    )
    sol=solve_reverse_logistics(s)
    # Exact oracle: open facility + process all 1000kg + 5km transport.
    expected=100 + 1000*2.0 + 1000*5*.01
    assert sol.objective_cost == pytest.approx(expected,abs=1e-5)
    assert sol.opened_facilities["R"]==1
    assert sol.processed_kg==pytest.approx(1000)
    assert sol.disposed_kg==pytest.approx(0,abs=1e-7)
