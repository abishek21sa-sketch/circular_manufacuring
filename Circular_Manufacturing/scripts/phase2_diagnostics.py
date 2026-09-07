from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from circular_battery.ai.training import train_all
root=Path(__file__).resolve().parents[1]
models,evidence,ds=train_all(root/"artifacts"/"models")
checks={}
checks["demand_beats_baseline_mae"]=evidence["demand"]["metrics"]["mae"] < evidence["demand"]["baseline_metrics"]["mae"]
checks["return_beats_baseline_brier"]=evidence["returns"]["metrics"]["brier"] < evidence["returns"]["baseline_metrics"]["brier"]
checks["recovery_beats_baseline_macro_f1"]=evidence["recovery"]["metrics"]["macro_f1"] > evidence["recovery"]["baseline_metrics"]["macro_f1"]
checks["scrap_beats_baseline_mae"]=evidence["scrap"]["metrics"]["mae"] < evidence["scrap"]["baseline_metrics"]["mae"]
checks["synthetic_labels"]=all(v["evidence_class"]=="SYNTHETIC VALIDATION" for v in evidence.values())
result={"phase":"PHASE-2","passed":all(checks.values()),"checks":checks,"evidence":evidence}
out=root/"docs"/"validation"/"phase2_diagnostics.json"; out.write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if result["passed"] else 1)
