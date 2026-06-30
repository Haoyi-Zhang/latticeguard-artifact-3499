#!/usr/bin/env python3
from __future__ import annotations
import csv, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.claim_traceability import write_claim_traceability

def read_csv(path: Path):
    with path.open('r', encoding='utf-8', newline='') as f: return list(csv.DictReader(f))

def main() -> None:
    report=write_claim_traceability(ROOT)
    rows=read_csv(ROOT/'results'/'claim_traceability_matrix.csv')
    errors=list(report.get('errors', []))
    if report.get('status')!='PASS': errors.append('claim traceability status is not PASS')
    if int(report.get('paper_visible_claims_traced',0)) < 30: errors.append('too few paper-visible claims traced')
    if any(r.get('trace_status')!='PASS' for r in rows): errors.append('claim traceability matrix contains failing row')
    for required in ['primary_evaluated_obligations','source_ids_covered','adapter_reference_agreement_rows','reference_integrity_entries','semantic_stress_witness_sources']:
        if required not in {r.get('claim_id') for r in rows}: errors.append(f'missing traced paper claim {required}')
    out={'status':'PASS' if not errors else 'FAIL','errors':errors,'report':report}
    print(json.dumps(out, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
