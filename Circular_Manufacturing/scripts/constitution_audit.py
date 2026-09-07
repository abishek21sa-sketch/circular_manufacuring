from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/"docs/validation/v1_compliance.json").read_text(encoding="utf-8"))
fail=[]
for r in p["requirements"]:
    path=ROOT/r["evidence"]
    if not path.exists(): fail.append({"capability":r["capability"],"reason":"missing evidence path","evidence":r["evidence"]})
    if r["status"] in {"PARTIAL","NOT_IMPLEMENTED"} or "NOT_IMPLEMENTED" in r["status"]:
        fail.append({"capability":r["capability"],"reason":"incomplete status","status":r["status"]})
out={"release":p["release"],"version":p["version"],"requirements":len(p["requirements"]),"passed":not fail,"failures":fail}
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["passed"] else 1)
