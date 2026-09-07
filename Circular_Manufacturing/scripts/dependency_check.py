from __future__ import annotations
import importlib.metadata, json, sys

MINIMUMS={
    "numpy":(2,0),
    "scipy":(1,13),
    "pandas":(2,2),
    "scikit-learn":(1,6),
    "pytest":(8,0),
}
def version_tuple(raw):
    parts=[]
    for token in raw.split("."):
        digits="".join(ch for ch in token if ch.isdigit())
        if not digits: break
        parts.append(int(digits))
    return tuple(parts)

checks={}
for pkg,minimum in MINIMUMS.items():
    try:
        raw=importlib.metadata.version(pkg)
        checks[pkg]={"version":raw,"minimum":".".join(map(str,minimum)),"passed":version_tuple(raw)>=minimum}
    except importlib.metadata.PackageNotFoundError:
        checks[pkg]={"version":None,"minimum":".".join(map(str,minimum)),"passed":False}

try:
    gv=importlib.metadata.version("gurobipy")
    checks["gurobipy"]={"version":gv,"minimum":"installed on licensed Windows acceptance target","passed":True}
except importlib.metadata.PackageNotFoundError:
    checks["gurobipy"]={"version":None,"minimum":"optional outside licensed Windows acceptance target","passed":sys.platform!="win32"}

out={"passed":all(x["passed"] for x in checks.values()),"python":sys.version.split()[0],"checks":checks}
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["passed"] else 1)
