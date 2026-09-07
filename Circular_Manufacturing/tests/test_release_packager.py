from pathlib import Path

from scripts.package_release import EXCLUDED_DIRECTORIES, EXCLUDED_FILENAMES, REQUIRED_ENTRIES


def test_release_packager_policy_excludes_runtime_and_nested_archives():
    assert {".git", ".venv", "__pycache__", ".pytest_cache"}.issubset(EXCLUDED_DIRECTORIES)
    assert {".env", ".coverage"}.issubset(EXCLUDED_FILENAMES)
    assert {".sqlite3", ".db", ".jsonl"}.issubset(__import__("scripts.package_release", fromlist=["EXCLUDED_SUFFIXES"]).EXCLUDED_SUFFIXES)
    assert Path("nested.zip").suffix.lower() == ".zip"
    assert any(entry.endswith("artifacts/release_readiness.json") for entry in REQUIRED_ENTRIES)
