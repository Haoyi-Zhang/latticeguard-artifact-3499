#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.benchmark_importers import native_subject_records, write_native_benchmark_suite, run_native_selftests

def main() -> None:
    records=native_subject_records()
    rows=write_native_benchmark_suite(ROOT/'subjects'/'native_public')
    selftests=run_native_selftests(ROOT/'subjects'/'native_public')
    errors=[]
    if len(records)<10: errors.append('expected at least 10 native subject records')
    if len(rows)<20: errors.append('expected at least 20 native fixture files')
    failures=[r for r in selftests if r.get('status')!='PASS']
    if failures: errors.append(f'native selftest failures: {len(failures)}')
    report={'status':'PASS' if not errors else 'FAIL','native_records':len(records),'native_fixture_files':len(rows),'native_selftests':len(selftests),'errors':errors,'records':[r.__dict__ for r in records]}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
