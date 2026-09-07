from __future__ import annotations
import hashlib, importlib.metadata, json, platform, sys
from pathlib import Path

DEPENDENCIES=("numpy","scipy","pandas","scikit-learn","joblib","gurobipy")

def dependency_versions():
    out={}
    for name in DEPENDENCIES:
        try: out[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: out[name]=None
    return out

def code_fingerprint(root: Path | str) -> str:
    root=Path(root)
    h=hashlib.sha256()
    files=list((root/"src").rglob("*.py"))+[root/"pyproject.toml"]
    for p in sorted(x for x in files if x.exists()):
        h.update(str(p.relative_to(root)).replace("\\","/").encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()

def environment_snapshot(root: Path | str):
    return {
        "python":sys.version.split()[0],
        "implementation":platform.python_implementation(),
        "platform":platform.platform(),
        "dependency_versions":dependency_versions(),
        "code_fingerprint_sha256":code_fingerprint(root),
    }
