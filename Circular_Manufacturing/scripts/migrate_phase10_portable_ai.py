from pathlib import Path
from circular_battery.maintenance.migrations import remove_deprecated_phase10_model_artifacts

ROOT = Path(__file__).resolve().parents[1]
removed = remove_deprecated_phase10_model_artifacts(ROOT)

print("PHASE10_PORTABLE_AI_MIGRATION_OK")
print(f"DEPRECATED_MODEL_FILES_REMOVED={len(removed)}")
for item in removed:
    print(f"REMOVED={item}")
