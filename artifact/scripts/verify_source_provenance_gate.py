#!/usr/bin/env python3
from __future__ import annotations
import csv, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.source_provenance_gate import write_source_provenance_gate

def read_csv(path: Path):
    with path.open('r', encoding='utf-8', newline='') as f: return list(csv.DictReader(f))

def main() -> None:
    report=write_source_provenance_gate(ROOT)
    rows=read_csv(ROOT/'results'/'source_provenance_gate.csv')
    errors=list(report.get('errors', []))
    if report.get('status')!='PASS': errors.append('source provenance report status is not PASS')
    if int(report.get('audited_subject_sources',0)) != 120: errors.append('audited source count must match current 120-source evaluation')
    if int(report.get('semantic_stress_witness_sources',0)) != 96: errors.append('semantic stress witness count must be explicit and stable')
    if int(report.get('generated_sources',0)) != 1: errors.append('generated source count must remain one')
    if len(rows) < 5: errors.append('provenance gate must expose at least five strata')
    stress=[r for r in rows if r.get('stratum')=='semantic_stress_witness']
    if not stress or 'not as independent upstream/public benchmark' not in stress[0].get('claim_safety_rule',''):
        errors.append('stress witness safety rule missing')
    out={'status':'PASS' if not errors else 'FAIL','errors':errors,'report':report}
    print(json.dumps(out, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
