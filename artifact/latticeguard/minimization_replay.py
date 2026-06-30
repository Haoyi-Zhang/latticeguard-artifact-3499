from __future__ import annotations
import json, hashlib
from pathlib import Path
from typing import Any


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(data: Any) -> str:
    return hashlib.sha256(stable_json(data).encode()).hexdigest()


def replay_counterexample_material(row: dict[str, Any]) -> tuple[bool, str]:
    required=['failure_id','adapter_id','relation_id','minimal_before_policy','minimal_after_policy','request','expected_invariant']
    missing=[k for k in required if k not in row]
    if missing:
        return False, 'missing:' + ','.join(missing)
    b=row['minimal_before_policy']; a=row['minimal_after_policy']; req=row['request']
    if not isinstance(b, dict) or not isinstance(a, dict) or not isinstance(req, dict):
        return False, 'minimal material has wrong shape'
    if len(b.get('rules',[])) + len(a.get('rules',[])) == 0:
        return False, 'empty minimal rule set cannot witness evaluator drift'
    return True, digest([row['failure_id'], row['adapter_id'], row['relation_id'], row.get('candidate_id',''), b, a, req])


def replay_all_counterexamples(root: Path) -> dict[str, Any]:
    path=root/'results'/'counterexamples.json'
    rows=json.loads(path.read_text(encoding='utf-8'))
    errors=[]; hashes=[]
    for row in rows:
        ok,h=replay_counterexample_material(row)
        if not ok: errors.append({'failure_id': row.get('failure_id','?'), 'reason': h})
        else: hashes.append(h)
    return {'status': 'PASS' if not errors else 'FAIL', 'counterexamples_checked': len(rows), 'errors': errors, 'digest': digest(sorted(hashes))}
