#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.reproducibility_contract import check_reproducibility_contract

def main() -> None:
    errors=check_reproducibility_contract(ROOT)
    sha=list(csv.DictReader((ROOT/'evidence'/'SHA256SUMS.csv').open())) if (ROOT/'evidence'/'SHA256SUMS.csv').exists() else []
    sources=list(csv.DictReader((ROOT/'source_manifest.csv').open())) if (ROOT/'source_manifest.csv').exists() else []
    if len(sha)<80: errors.append('SHA-256 ledger too shallow for optimized repository')
    if len(sources)<40: errors.append('source manifest too shallow for optimized repository')
    report={'status':'PASS' if not errors else 'FAIL','required_paths_checked':7,'sha256_rows':len(sha),'source_manifest_rows':len(sources),'errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
