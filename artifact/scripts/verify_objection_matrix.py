#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.objection_matrix import objection_rows

def main():
    rows=objection_rows(ROOT/'results'/'summary.json')
    out=ROOT/'results'/'audit_objection_matrix.csv'
    with out.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=['lens','objection','evidence_file','repair_status','residual_risk'])
        w.writeheader(); w.writerows(rows)
    missing=[r for r in rows if not (ROOT/r['evidence_file']).exists()]
    report={'status':'PASS' if not missing and len(rows)>=7 else 'FAIL','objections':len(rows),'missing_evidence':missing}
    print(json.dumps(report, indent=2, sort_keys=True))
    if report['status']!='PASS': raise SystemExit(1)
if __name__=='__main__': main()
