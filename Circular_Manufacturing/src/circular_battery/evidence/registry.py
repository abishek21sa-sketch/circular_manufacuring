from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

def stable_hash(obj)->str:
    raw=json.dumps(obj,sort_keys=True,separators=(',',':'),default=str).encode()
    return hashlib.sha256(raw).hexdigest()

def write_run_record(report:dict, directory:Path|str):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    decision_hash=stable_hash({
        'release':report.get('release'),'seed':report.get('seed'),
        'recommended_policy':report.get('decision',{}).get('recommended_policy'),
        'ai_bridge':report.get('ai_to_or_bridge'),
    })
    record={
        'run_id':decision_hash[:16],
        'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'release':report.get('release'),'version':report.get('version'),
        'decision_hash_sha256':decision_hash,
        'evidence_classes':sorted(set(report.get('evidence_classes',[]))),
        'seed':report.get('seed'),
        'tests_claimed':None,
    }
    p=directory/f"{record['run_id']}.json";p.write_text(json.dumps(record,indent=2),encoding='utf-8')
    return record,p
