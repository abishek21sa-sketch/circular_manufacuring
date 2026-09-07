from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
import sys
if str(ROOT/'src') not in sys.path:
    sys.path.insert(0,str(ROOT/'src'))

from circular_battery.decision.circular_mass_bridge import build_circular_mass_decision, circular_mass_reference_payload

OUT=ROOT/'artifacts'/'circular_mass'
OUT.mkdir(parents=True,exist_ok=True)

reference=circular_mass_reference_payload()
decision=build_circular_mass_decision()
stress=build_circular_mass_decision(min_recycled_content=.65)
checks={
    'reference_validation_present': reference.get('validation') is not None,
    'reference_authorized': decision['decision_gate']=='AUTHORIZED',
    'human_review_mandatory': decision['human_review_required'] is True,
    'reference_mass_balance_feasible': decision['checks']['mass_balance_feasible'],
    'high_circularity_policy_met': stress['solution']['recycled_content_share'] >= .65-1e-8,
    'high_circularity_uses_at_least_as_much_recovery': stress['solution']['expected_recovered_kg'] >= decision['solution']['expected_recovered_kg'],
    'stable_decision_identifier': build_circular_mass_decision()['decision_id']==decision['decision_id'],
}
payload={
    'algorithm':'CIRCULAR-MASS',
    'evidence_class':'DETERMINISTIC SYNTHETIC PRODUCT-INTEGRATION VALIDATION',
    'reference_decision':decision,
    'high_circularity_counterfactual':stress,
    'checks':checks,
}
(OUT/'product_decision_evidence.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
report=['# CIRCULAR-MASS Product Integration Evidence','',f"Decision ID: `{decision['decision_id']}`",f"Decision gate: **{decision['decision_gate']}**",f"Human review required: **{decision['human_review_required']}**",'', '## Checks']
report += [f"- {'PASS' if v else 'FAIL'} — {k.replace('_',' ')}" for k,v in checks.items()]
report += ['', '## Evidence boundary', decision['evidence']['class'], '', decision['tail_risk_note']]
(OUT/'PRODUCT_INTEGRATION_REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
passed=sum(bool(v) for v in checks.values())
print(f'CIRCULAR_MASS_PRODUCT_EVIDENCE={passed}/{len(checks)}')
print(f"CIRCULAR_MASS_DECISION_ID={decision['decision_id']}")
print(f"CIRCULAR_MASS_GATE={decision['decision_gate']}")
if passed != len(checks):
    raise SystemExit(1)
