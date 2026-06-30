#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.oracle_catalog import relation_table, validate_relation_catalog

def main() -> None:
    errors=validate_relation_catalog()
    out=ROOT/'results'/'relation_catalog_expanded.csv'
    rows=relation_table()
    if out.exists():
        with out.open('r',encoding='utf-8',newline='') as f: observed=list(csv.DictReader(f))
        if observed!=rows: errors.append('relation catalog ledger differs from library catalog')
    report={'status':'PASS' if not errors else 'FAIL','relations':len(rows),'catalog_path':'results/relation_catalog_expanded.csv','errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
