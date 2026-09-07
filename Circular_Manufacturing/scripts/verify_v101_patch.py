from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from circular_battery import __version__
from circular_battery.platform.storage import RunStore

ROOT = Path(__file__).resolve().parents[1]

checks = {}
checks["runtime_version_1_0_1"] = __version__ == "1.0.1"
checks["pyproject_version_1_0_1"] = 'version = "1.0.1"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
storage_text = (ROOT / "src/circular_battery/platform/storage.py").read_text(encoding="utf-8")
checks["explicit_connection_context"] = "def _connection(self):" in storage_text
checks["no_direct_connection_context_usage"] = "with self._connect() as con" not in storage_text

# Exercise the exact Windows failure mode: create a SQLite DB, use it through
# RunStore, then immediately delete the containing directory. Windows only
# allows this if every SQLite handle has really been closed.
td = Path(tempfile.mkdtemp(prefix="circular-v101-delete-check-"))
try:
    db = td / "diag.sqlite3"
    store = RunStore(db)
    scenario = store.create_scenario({
        "name": "windows-delete-check",
        "seed": 1,
        "raw_n": 30,
        "reduced_k": 5,
        "include_sensitivity": False,
        "notes": "",
    })
    run_id = store.start_run(scenario["scenario_id"], "fingerprint")
    store.complete_run(
        run_id,
        {"decision_hash_sha256": "delete-check", "decision": {"recommended_policy": "resilience"}},
        0.001,
    )
    store.health()
    store.get_run(run_id)
    store.list_runs()
    store.audit_events()
finally:
    try:
        shutil.rmtree(td)
        checks["sqlite_directory_deletable_after_store_operations"] = True
    except PermissionError:
        checks["sqlite_directory_deletable_after_store_operations"] = False

print("Circular Manufacturing V1.0.1 patch verification")
for name, passed in checks.items():
    print(f"{name.upper()}={passed}")

if not all(checks.values()):
    raise SystemExit(1)
print("V101_PATCH_VERIFIED")
