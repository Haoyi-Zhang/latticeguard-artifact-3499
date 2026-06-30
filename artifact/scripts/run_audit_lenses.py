#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.evidence_queries import summarize_evidence
from latticeguard.audit_lenses import score_lenses

def main() -> None:
    summary=summarize_evidence(ROOT); lenses=score_lenses(summary); blockers=[b for l in lenses for b in l.get('blocking_issues',[])]
    report={'status':'PASS' if not blockers else 'FAIL','mean_score':sum(l['score'] for l in lenses)/len(lenses),'lenses':lenses,'blocking_issues':blockers}
    print(json.dumps(report, indent=2, sort_keys=True))
    if blockers: raise SystemExit(1)
if __name__=='__main__': main()
