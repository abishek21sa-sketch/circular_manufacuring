from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
record=json.loads((ROOT/'docs/validation/locked_phase10_core_comparison.json').read_text(encoding='utf-8'))
fail=[]
for item in record['files']:
    p=ROOT/item['file']
    if not p.is_file(): fail.append({'file':item['file'],'reason':'missing'}); continue
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual!=item['sha256']: fail.append({'file':item['file'],'reason':'hash_mismatch','expected':item['sha256'],'actual':actual})
out={'passed':not fail,'baseline':record['baseline'],'verified_files':len(record['files']),'failures':fail}
print(json.dumps(out,indent=2))
raise SystemExit(0 if out['passed'] else 1)
