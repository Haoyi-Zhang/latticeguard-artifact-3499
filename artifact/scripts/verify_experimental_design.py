#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.experimental_design import design_matrix

def main():
    rows=design_matrix(ROOT)
    out=ROOT/'results'/'experimental_design_matrix.csv'
    with out.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=['stream','metric','value','audit_question']); w.writeheader(); w.writerows(rows)
    errors=[]
    vals={r['metric']: int(r['value']) for r in rows if str(r['value']).isdigit()}
    if vals.get('primary_evaluated_obligations',0)<2500: errors.append('primary obligations below design target')
    if vals.get('minimized_counterexamples',0)<1500: errors.append('counterexamples below design target')
    if vals.get('native_selftest_rows',0)<400: errors.append('native selftests below design target')
    report={'status':'PASS' if not errors else 'FAIL','errors':errors,'rows':len(rows)}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
