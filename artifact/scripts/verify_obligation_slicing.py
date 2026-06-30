#!/usr/bin/env python3
import csv, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.obligation_slicing import slice_matrix
rows=slice_matrix(ROOT)
path=ROOT/'results'/'obligation_slice_matrix.csv'
with path.open('w', newline='', encoding='utf-8') as f:
    w=csv.DictWriter(f, fieldnames=['adapter_id','relation_id','sources','obligations','passes','status']); w.writeheader(); w.writerows(rows)
fail=[r for r in rows if r['status']!='PASS']
out={'rows':len(rows),'failures':len(fail),'status':'PASS' if not fail else 'FAIL'}
print(json.dumps(out, indent=2, sort_keys=True))
if fail: raise SystemExit(1)
