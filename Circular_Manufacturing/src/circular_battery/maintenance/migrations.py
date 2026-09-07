from __future__ import annotations
from pathlib import Path

DEPRECATED_MODEL_GLOB = "*_model.joblib"

def remove_deprecated_phase10_model_artifacts(root: Path) -> list[str]:
    """Remove legacy sklearn estimator binaries superseded by runtime retraining.

    This migration is intentionally narrow: only files matching
    artifacts/models/*_model.joblib are removed. JSON evidence and all other
    artifacts are preserved. The operation is idempotent.
    """
    model_dir = root / "artifacts" / "models"
    removed: list[str] = []
    if not model_dir.exists():
        return removed
    for path in sorted(model_dir.glob(DEPRECATED_MODEL_GLOB)):
        if path.is_file():
            path.unlink()
            removed.append(path.relative_to(root).as_posix())
    return removed
