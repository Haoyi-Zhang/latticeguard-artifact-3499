#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.result_invariants import check_result_invariants

def main() -> None:
    errors=check_result_invariants(ROOT)
    flat=[x for v in errors.values() for x in v]
    report={'status':'PASS' if not flat else 'FAIL','sections':{k:len(v) for k,v in errors.items()},'errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if flat: raise SystemExit(1)
if __name__=='__main__': main()
