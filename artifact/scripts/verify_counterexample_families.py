#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main() -> None:
    rows=json.loads((ROOT/'results'/'counterexamples.json').read_text(encoding='utf-8'))
    errors=[]
    if not rows: errors.append('no counterexamples')
    rels=Counter(r['relation_id'] for r in rows); adapters=Counter(r['adapter_id'] for r in rows); sources=Counter(r.get('source_id','') for r in rows)
    if len(adapters)<5: errors.append('counterexamples do not cover seeded mutant families')
    if len(sources)<10: errors.append('counterexamples do not cover benchmark sources')
    report={'status':'PASS' if not errors else 'FAIL','counterexamples':len(rows),'relations_with_counterexamples':len(rels),'sources_with_counterexamples':len(sources),'adapters_with_counterexamples':dict(adapters),'errors':errors}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
