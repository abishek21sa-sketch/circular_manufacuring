from __future__ import annotations
import json, threading
from datetime import datetime, timezone
from pathlib import Path
import re


_SENSITIVE_KEY = re.compile(
    r"(?:token|authorization|password|passwd|secret|api[_-]?key|private[_-]?key|dsn|database[_-]?url)",
    re.IGNORECASE,
)
_CREDENTIAL_IN_URL = re.compile(r"(?i)(://[^/:\s]+:)[^@\s]+(@)")
_BEARER = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/=-]+")


def _safe_value(key: str, value):
    """Redact credential-bearing fields before they reach durable logs."""
    if _SENSITIVE_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _safe_value(str(k), v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_value(key, item) for item in value]
    if isinstance(value, str):
        value = _CREDENTIAL_IN_URL.sub(r"\1[REDACTED]\2", value)
        return _BEARER.sub(r"\1[REDACTED]", value)
    return value

class JsonlEventLogger:
    def __init__(self, path: Path | str):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self._lock=threading.Lock()

    def emit(self, event_type: str, **fields):
        row={
            "timestamp_utc":datetime.now(timezone.utc).isoformat(),
            "event_type":event_type,
            **{str(key): _safe_value(str(key), value) for key, value in fields.items()},
        }
        raw=json.dumps(row,sort_keys=True,default=str)
        with self._lock:
            with self.path.open("a",encoding="utf-8") as f:
                f.write(raw+"\n")
        return row
