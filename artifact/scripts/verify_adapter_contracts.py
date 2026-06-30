#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.adapter_contracts import ADAPTER_CONTRACTS, validate_adapter_contracts

def main() -> None:
    errors=validate_adapter_contracts()
    report={'status':'PASS' if not errors else 'FAIL','contracts_checked':len(ADAPTER_CONTRACTS),'errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
