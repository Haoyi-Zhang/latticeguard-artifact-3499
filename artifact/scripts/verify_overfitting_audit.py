#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.overfitting_audit import build_overfitting_audit

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def main():
    rows, report = build_overfitting_audit(ROOT)
    write_csv(ROOT/'results'/'overfitting_audit.csv', rows, ['source_id','split','source_manifest_kind','adapter_count','relation_count','evaluated_obligations','rejected_rows','unsupported_rows','predicate_candidates','predicate_witness_hashes','candidate_shape_families','status'])
    (ROOT/'results'/'overfitting_audit.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2, sort_keys=True))
    if report.get('status') != 'PASS':
        raise SystemExit(1)
if __name__ == '__main__': main()
