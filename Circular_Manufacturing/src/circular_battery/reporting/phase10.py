from pathlib import Path
import json
from circular_battery.decision.orchestrator import build_phase10_decision
from circular_battery.evidence.registry import write_run_record

def write_phase10_report(path='artifacts/phase10_decision_report.json', seed=20260817, raw_n=80, reduced_k=10):
    report=build_phase10_decision(seed=seed,raw_n=raw_n,reduced_k=reduced_k)
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(report,indent=2),encoding='utf-8')
    record,record_path=write_run_record(report,p.parent/'run_registry')
    return report,record,record_path
