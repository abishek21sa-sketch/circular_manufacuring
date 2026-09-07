from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
    "private_key":re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "google_api_key":re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
    "openai_style_key":re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    "gurobi_license_id_from_validation_host":re.compile(r"\b2787943\b"),
}
SKIP_SUFFIXES={".pyc",".png",".jpg",".jpeg",".zip",".whl",".sqlite3",".db"}
hits=[]
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix.lower() in SKIP_SUFFIXES: continue
    if ".venv" in p.parts: continue
    try: text=p.read_text(encoding="utf-8",errors="ignore")
    except Exception: continue
    for name,pattern in PATTERNS.items():
        if pattern.search(text):
            hits.append({"file":p.relative_to(ROOT).as_posix(),"pattern":name})

tracked_env=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob(".env") if ".venv" not in p.parts]
result={"passed":not hits and not tracked_env,"secret_pattern_findings":hits,"tracked_env_files":tracked_env}
print(json.dumps(result,indent=2))
raise SystemExit(0 if result["passed"] else 1)
