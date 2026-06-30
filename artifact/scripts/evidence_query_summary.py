#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.evidence_queries import summarize_evidence

def main() -> None:
    summary=summarize_evidence(ROOT)
    errors=[]
    if summary['evaluated_obligations'] != summary['passes'] + summary['failures']:
        errors.append('primary obligation accounting mismatch')
    if summary['soundness_failures'] != 0:
        errors.append('soundness failures present')
    report={'status':'PASS' if not errors else 'FAIL','claim_errors':errors,'summary':summary}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
