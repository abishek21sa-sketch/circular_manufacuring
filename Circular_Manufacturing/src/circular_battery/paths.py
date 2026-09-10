"""Repo-root resolution that survives a non-editable install.

Every module that reads a repo-relative asset (artifacts/, data/public/, etc.)
used to compute its own `ROOT = Path(__file__).resolve().parents[3]`. That
assumes `__file__` sits inside the source tree, which is only true for an
editable install (`pip install -e .`). Render's build (`pip install
".[gurobi,postgres]"`, no `-e`) copies this package into
`.venv/lib/python3.14/site-packages/circular_battery/...`, so `__file__`
resolves there instead -- `parents[3]` from a file two levels under
`site-packages` lands inside `.venv/lib/python3.14/`, not the repo root, and
every one of those reads throws `FileNotFoundError` in production (confirmed
live: `/api/v1/workbench` and `/api/v1/public-reference/*` both 500 with
exactly this traceback).

`scripts/run_workbench.py` is always launched with the repo root as the
process's current working directory (locally and on Render, per
render.yaml's `startCommand`), so `Path.cwd()` is reliable there regardless of
install mode. The `__file__` walk-up is kept only as a fallback for contexts
that don't guarantee that (e.g. a test invoked from an unrelated cwd against
an editable install).
"""

from __future__ import annotations

from pathlib import Path

_MARKER = "pyproject.toml"


def find_repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / _MARKER).is_file():
        return cwd
    for parent in Path(__file__).resolve().parents:
        if (parent / _MARKER).is_file():
            return parent
    raise RuntimeError(
        f"Could not locate the circular_battery repo root (no {_MARKER} found "
        f"under cwd {cwd} or any parent of {__file__})"
    )
