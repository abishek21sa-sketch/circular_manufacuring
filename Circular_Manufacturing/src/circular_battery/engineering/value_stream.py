from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class RecoveryStep:
    name: str
    processing_hours: float
    waiting_hours: float
    yield_rate: float

def analyze_recovery_value_stream(steps):
    if not steps:
        raise ValueError("At least one recovery step is required.")
    for s in steps:
        if s.processing_hours < 0 or s.waiting_hours < 0 or not (0 <= s.yield_rate <= 1):
            raise ValueError("Invalid value-stream step.")
    va = sum(s.processing_hours for s in steps)
    lead = sum(s.processing_hours + s.waiting_hours for s in steps)
    cumulative_yield = 1.0
    for s in steps:
        cumulative_yield *= s.yield_rate
    return {
        "value_added_hours": va,
        "total_lead_time_hours": lead,
        "process_cycle_efficiency": va / lead if lead else 0.0,
        "cumulative_recovery_yield": cumulative_yield,
        "bottleneck_wait_step": max(steps, key=lambda s: s.waiting_hours).name,
        "evidence_class": "CALCULATED",
    }
