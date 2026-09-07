from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from circular_battery.evidence.registry import stable_hash
from circular_battery.platform.errors import NotFoundError, ConflictError

SCHEMA_VERSION = 1


def _now():
    return datetime.now(timezone.utc).isoformat()


class RunStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.initialize()

    def _connect(self):
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA journal_mode=WAL")
        return con

    @contextmanager
    def _connection(self):
        """Transactional SQLite connection that is always explicitly closed.

        sqlite3.Connection's own context manager commits/rolls back but does
        not close the connection. Explicit close is mandatory for Windows,
        where an open SQLite handle prevents temporary/database file cleanup.
        """
        con = self._connect()
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def initialize(self):
        with self._lock, self._connection() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scenarios (
                scenario_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at_utc TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                config_json TEXT NOT NULL,
                config_hash_sha256 TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                scenario_id TEXT,
                created_at_utc TEXT NOT NULL,
                completed_at_utc TEXT,
                status TEXT NOT NULL,
                runtime_seconds REAL,
                decision_hash_sha256 TEXT,
                code_fingerprint_sha256 TEXT,
                report_json TEXT,
                error_json TEXT,
                FOREIGN KEY(scenario_id) REFERENCES scenarios(scenario_id)
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at_utc TEXT NOT NULL,
                event_type TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                details_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at_utc DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at_utc DESC);
            """)
            con.execute(
                "INSERT OR REPLACE INTO metadata(key,value) VALUES('schema_version',?)",
                (str(SCHEMA_VERSION),),
            )

    def health(self):
        with self._connection() as con:
            row = con.execute(
                "SELECT value FROM metadata WHERE key='schema_version'"
            ).fetchone()
        return {
            "database": "ok",
            "schema_version": int(row["value"]),
            "path": str(self.path),
        }

    def audit(self, event_type, entity_type, entity_id=None, details=None):
        with self._lock, self._connection() as con:
            con.execute(
                "INSERT INTO audit_events(created_at_utc,event_type,entity_type,entity_id,details_json) "
                "VALUES(?,?,?,?,?)",
                (
                    _now(),
                    event_type,
                    entity_type,
                    entity_id,
                    json.dumps(details or {}, sort_keys=True, default=str),
                ),
            )

    def create_scenario(self, config: dict):
        scenario_id = "scn_" + uuid.uuid4().hex[:16]
        now = _now()
        config_json = json.dumps(config, sort_keys=True, default=str)
        h = stable_hash(config)
        with self._lock, self._connection() as con:
            con.execute(
                "INSERT INTO scenarios(scenario_id,name,created_at_utc,updated_at_utc,"
                "config_json,config_hash_sha256,notes) VALUES(?,?,?,?,?,?,?)",
                (
                    scenario_id,
                    config["name"],
                    now,
                    now,
                    config_json,
                    h,
                    config.get("notes", ""),
                ),
            )
        self.audit(
            "scenario.created",
            "scenario",
            scenario_id,
            {"config_hash_sha256": h},
        )
        return self.get_scenario(scenario_id)

    def import_scenario(self, record: dict):
        config = record.get("config", record)
        return self.create_scenario(config)

    def get_scenario(self, scenario_id):
        with self._connection() as con:
            row = con.execute(
                "SELECT * FROM scenarios WHERE scenario_id=?",
                (scenario_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"Scenario {scenario_id} not found.")
        return {
            "scenario_id": row["scenario_id"],
            "name": row["name"],
            "created_at_utc": row["created_at_utc"],
            "updated_at_utc": row["updated_at_utc"],
            "config": json.loads(row["config_json"]),
            "config_hash_sha256": row["config_hash_sha256"],
            "notes": row["notes"],
        }

    def list_scenarios(self, limit=50):
        limit = max(1, min(int(limit), 200))
        with self._connection() as con:
            rows = con.execute(
                "SELECT scenario_id,name,created_at_utc,updated_at_utc,"
                "config_hash_sha256,notes FROM scenarios "
                "ORDER BY created_at_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_scenario(self, scenario_id):
        self.get_scenario(scenario_id)
        with self._lock, self._connection() as con:
            attached = con.execute(
                "SELECT COUNT(*) AS n FROM runs WHERE scenario_id=?",
                (scenario_id,),
            ).fetchone()["n"]
            if attached:
                raise ConflictError(
                    "Scenario has persisted decision runs and cannot be deleted.",
                    details={"run_count": attached},
                )
            con.execute(
                "DELETE FROM scenarios WHERE scenario_id=?",
                (scenario_id,),
            )
        self.audit("scenario.deleted", "scenario", scenario_id)

    def start_run(self, scenario_id, code_fingerprint, *, request_id=None, actor_role=None):
        if scenario_id is not None:
            self.get_scenario(scenario_id)
        run_id = "run_" + uuid.uuid4().hex[:16]
        with self._lock, self._connection() as con:
            con.execute(
                "INSERT INTO runs(run_id,scenario_id,created_at_utc,status,"
                "code_fingerprint_sha256) VALUES(?,?,?,?,?)",
                (run_id, scenario_id, _now(), "RUNNING", code_fingerprint),
            )
        self.audit(
            "run.started",
            "run",
            run_id,
            {
                "scenario_id": scenario_id,
                "request_id": request_id,
                "actor_role": actor_role or "unknown",
            },
        )
        return run_id

    def complete_run(self, run_id, report, runtime_seconds):
        decision_hash = report.get("decision_hash_sha256")
        with self._lock, self._connection() as con:
            con.execute(
                "UPDATE runs SET completed_at_utc=?,status='COMPLETED',"
                "runtime_seconds=?,decision_hash_sha256=?,report_json=?,"
                "error_json=NULL WHERE run_id=?",
                (
                    _now(),
                    float(runtime_seconds),
                    decision_hash,
                    json.dumps(report, sort_keys=True, default=str),
                    run_id,
                ),
            )
        self.audit(
            "run.completed",
            "run",
            run_id,
            {
                "decision_hash_sha256": decision_hash,
                "runtime_seconds": runtime_seconds,
            },
        )

    def fail_run(self, run_id, error):
        # Exception text can contain provider details or user-supplied secrets.
        # Keep the durable record useful for triage without persisting raw text.
        payload = {"type": type(error).__name__}
        with self._lock, self._connection() as con:
            con.execute(
                "UPDATE runs SET completed_at_utc=?,status='FAILED',error_json=? "
                "WHERE run_id=?",
                (_now(), json.dumps(payload, sort_keys=True), run_id),
            )
        self.audit("run.failed", "run", run_id, payload)

    def get_run(self, run_id, include_report=True):
        with self._connection() as con:
            row = con.execute(
                "SELECT * FROM runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"Run {run_id} not found.")
        out = {
            "run_id": row["run_id"],
            "scenario_id": row["scenario_id"],
            "created_at_utc": row["created_at_utc"],
            "completed_at_utc": row["completed_at_utc"],
            "status": row["status"],
            "runtime_seconds": row["runtime_seconds"],
            "decision_hash_sha256": row["decision_hash_sha256"],
            "code_fingerprint_sha256": row["code_fingerprint_sha256"],
            "error": json.loads(row["error_json"]) if row["error_json"] else None,
        }
        if include_report:
            out["report"] = (
                json.loads(row["report_json"]) if row["report_json"] else None
            )
        return out

    def list_runs(self, limit=50):
        limit = max(1, min(int(limit), 200))
        with self._connection() as con:
            rows = con.execute(
                "SELECT run_id,scenario_id,created_at_utc,completed_at_utc,status,"
                "runtime_seconds,decision_hash_sha256,code_fingerprint_sha256 "
                "FROM runs ORDER BY created_at_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def audit_events(self, limit=100):
        limit = max(1, min(int(limit), 500))
        with self._connection() as con:
            rows = con.execute(
                "SELECT * FROM audit_events ORDER BY event_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d.pop("details_json"))
            out.append(d)
        return out
