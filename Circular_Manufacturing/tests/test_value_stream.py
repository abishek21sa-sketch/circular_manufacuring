import pytest
from circular_battery.engineering.value_stream import RecoveryStep, analyze_recovery_value_stream

def test_pce_reference_case():
    r = analyze_recovery_value_stream([
        RecoveryStep("a",2,6,.9),
        RecoveryStep("b",3,9,.8),
    ])
    assert r["value_added_hours"] == 5
    assert r["total_lead_time_hours"] == 20
    assert r["process_cycle_efficiency"] == pytest.approx(.25)
    assert r["cumulative_recovery_yield"] == pytest.approx(.72)
    assert r["bottleneck_wait_step"] == "b"
