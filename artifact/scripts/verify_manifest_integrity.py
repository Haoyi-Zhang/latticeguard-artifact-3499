#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
sys.dont_write_bytecode = True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.manifest_integrity import verify_sha_manifest

def main() -> None:
    errors=verify_sha_manifest(ROOT)
    sources=list(csv.DictReader((ROOT/'source_manifest.csv').open()))
    for r in sources:
        if not r.get('sha256'): errors.append('source row missing sha256 '+r.get('source_id','?'))
    report={'status':'PASS' if not errors else 'FAIL','sha256_checked':len(list(csv.DictReader((ROOT/'evidence'/'SHA256SUMS.csv').open()))),'source_manifest_checked':len(sources),'errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
