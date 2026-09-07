from __future__ import annotations
from datetime import datetime, timezone

API_VERSION = "v1"
SCHEMA_VERSION = "1.0"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def success(data, *, request_id: str, meta: dict | None = None):
    return {
        "ok":True,
        "api_version":API_VERSION,
        "schema_version":SCHEMA_VERSION,
        "request_id":request_id,
        "timestamp_utc":utc_now(),
        "data":data,
        "meta":meta or {},
    }

def failure(code: str, message: str, *, request_id: str, details: dict | None = None):
    return {
        "ok":False,
        "api_version":API_VERSION,
        "schema_version":SCHEMA_VERSION,
        "request_id":request_id,
        "timestamp_utc":utc_now(),
        "error":{"code":code,"message":message,"details":details or {}},
    }
