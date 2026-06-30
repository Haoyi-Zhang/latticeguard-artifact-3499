from __future__ import annotations
import csv
from pathlib import Path

def source_sets(root: Path) -> dict[str,set[str]]:
    def rows(p):
        with p.open('r',encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
    manifest={r['source_id'] for r in rows(root/'source_manifest.csv') if r.get('kind')=='subject_seed'}
    obligations={r['source_id'] for r in rows(root/'results'/'obligations.csv')}
    coverage={r['source_id'] for r in rows(root/'results'/'coverage.csv')}
    return {'manifest':manifest,'obligations':obligations,'coverage':coverage}
def linkage_errors(root: Path) -> list[str]:
    s=source_sets(root); return [] if s['obligations']<=s['manifest'] and s['coverage']<=s['manifest'] else ['source linkage mismatch']
