#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.benchmark_funnel import build_funnel

def main() -> None:
    rows=build_funnel(ROOT)
    errors=[]
    if len(rows)<17: errors.append('too few included benchmark/source rows')
    class_counts={}
    for r in rows: class_counts[r['kind']]=class_counts.get(r['kind'],0)+1
    if class_counts.get('native_public_fixture',0)<20: errors.append('native fixture file coverage too shallow')
    report={'status':'PASS' if not errors else 'FAIL','source_manifest_rows':len(list(csv.DictReader((ROOT/'source_manifest.csv').open()))),'benchmark_sources':len(rows),'class_counts':class_counts,'errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
