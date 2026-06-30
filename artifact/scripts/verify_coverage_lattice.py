#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.coverage_lattice import coverage_rows, density

def main() -> None:
    rows=coverage_rows(ROOT); d=density(rows); errors=[]
    adapters=len({r['adapter_id'] for r in rows}); sources=len({r['source_id'] for r in rows}); rels=len({r['relation_id'] for r in rows})
    if d < 1.0: errors.append('coverage lattice not complete')
    report={'status':'PASS' if not errors else 'FAIL','density':d,'covered_cells':sum(r['covered']=='true' for r in rows),'total_cells':len(rows),'adapters':adapters,'sources':sources,'relations':rels,'errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
