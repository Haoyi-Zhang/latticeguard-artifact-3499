#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.schemas import validate_repository_schemas, read_csv, assert_no_hidden_denominator

def main() -> None:
    errors=validate_repository_schemas(ROOT)
    if (ROOT/'results'/'obligations.csv').exists():
        errors.extend(assert_no_hidden_denominator(read_csv(ROOT/'results'/'obligations.csv')))
    report={'status':'PASS' if not errors else 'FAIL','p0_count':len(errors),'p1_count':0,'issues':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
