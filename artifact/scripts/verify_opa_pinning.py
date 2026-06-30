#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.opa_pinning import inspect_opa_candidate, EXPECTED_SHA

def main() -> None:
    c=inspect_opa_candidate(ROOT); errors=[]
    if c['exists'] and c['sha256'] != EXPECTED_SHA: errors.append('OPA binary hash does not match pinned SHA-256')
    report={'status':'PASS' if not errors else 'FAIL','expected_sha256':EXPECTED_SHA,'selected':c if c['status']=='READY' else None,'candidates':[c],'errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
