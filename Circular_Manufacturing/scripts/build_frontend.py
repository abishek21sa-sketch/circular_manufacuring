from pathlib import Path
import os
import shutil, subprocess
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"web"/"src"; DIST=ROOT/"web"/"dist"
DIST.mkdir(parents=True,exist_ok=True)
for name in ("index.html","styles.css"):
    shutil.copy2(SRC/name,DIST/name)


def _local_tsc() -> Path | None:
    suffix = ".cmd" if os.name == "nt" else ""
    candidate = ROOT / "web" / "node_modules" / ".bin" / f"tsc{suffix}"
    return candidate if candidate.exists() else None


def _ensure_toolchain() -> Path:
    local = _local_tsc()
    if local:
        return local

    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm") or shutil.which("npm")
    lockfile = ROOT / "web" / "package-lock.json"
    if npm and lockfile.exists():
        print("Frontend TypeScript toolchain missing; installing from package-lock.json", flush=True)
        result = subprocess.run(
            [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=ROOT / "web",
        )
        if result.returncode:
            raise SystemExit(result.returncode)
        local = _local_tsc()
        if local:
            return local

    global_tsc = shutil.which("tsc")
    if global_tsc:
        return Path(global_tsc)
    raise RuntimeError(
        "TypeScript compiler unavailable. Run 'npm ci --ignore-scripts --no-audit --no-fund' "
        "in web, then rerun scripts/build_frontend.py."
    )


tsc = _ensure_toolchain()
result = subprocess.run([str(tsc), "-p", str(ROOT / "web" / "tsconfig.json")], cwd=ROOT)
if result.returncode:
    raise SystemExit(result.returncode)
print("FRONTEND_BUILD_MODE=typescript-source")
print(f"FRONTEND_BUILT={DIST}")
