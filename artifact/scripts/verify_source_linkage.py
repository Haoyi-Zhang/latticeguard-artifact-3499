#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.source_linkage import source_sets, linkage_errors

def main() -> None:
    sets=source_sets(ROOT); errors=linkage_errors(ROOT)
    report={'status':'PASS' if not errors else 'FAIL','manifest_subjects':len(sets['manifest']),'obligation_subjects':len(sets['obligations']),'coverage_subjects':len(sets['coverage']),'native_benchmark_subjects':len([s for s in sets['manifest'] if s.startswith('public_native_')]),'errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
