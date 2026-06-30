from __future__ import annotations
import csv
from pathlib import Path

def write_drift_mining_harness(root: Path) -> list[dict[str,str]]:
    rows=[{'source_id':'none_counted','before_version':'','after_version':'','public_url':'','license':'','status':'NO_PUBLIC_RELEASE_PAIR_SEED_PROVIDED','counted_real_drift_witness':'false','note':'Harness requires public before/after fixture, license, and replay material before a real drift claim may be counted.'}]
    out=root/'results'/'drift_mining.csv'
    with out.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows

def summarize_drift(rows:list[dict[str,str]]) -> dict[str,int]:
    return {'public_release_pair_seeds': sum(1 for r in rows if r.get('public_url')), 'counted_real_drift_witnesses': sum(1 for r in rows if r.get('counted_real_drift_witness')=='true')}
