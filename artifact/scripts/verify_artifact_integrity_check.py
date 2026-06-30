#!/usr/bin/env python3
from __future__ import annotations
import sys

sys.dont_write_bytecode = True

import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0,str(ROOT))
from latticeguard.artifact_integrity_check import package_gate
from latticeguard.runtime_hygiene import cleanup_bytecode_artifacts, scan_bytecode_artifacts
from scripts.create_artifact_bundle import build_manifest
import csv

def _ensure_manifest():
    target = ROOT/'results'/'artifact_manifest.csv'
    rows = build_manifest()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['path','bytes','included','reason'])
        w.writeheader(); w.writerows(rows)

def main():
    removed = cleanup_bytecode_artifacts(ROOT)
    _ensure_manifest()
    report = package_gate(ROOT)
    removed += cleanup_bytecode_artifacts(ROOT)
    remaining = [path.relative_to(ROOT).as_posix() for path in scan_bytecode_artifacts(ROOT)]
    if remaining:
        report = dict(report)
        report['status'] = 'FAIL'
        report['errors'] = list(report.get('errors', [])) + [f'bytecode residue remains after cleanup: {", ".join(remaining[:20])}']
    report['bytecode_cleanup_removed'] = len(removed)
    report['bytecode_residue_remaining'] = len(remaining)
    (ROOT/'results'/'artifact_integrity_check.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2, sort_keys=True))
    if report['status']!='PASS': raise SystemExit(1)
if __name__=='__main__': main()
