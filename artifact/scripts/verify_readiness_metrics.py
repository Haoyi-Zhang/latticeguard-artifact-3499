#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.readiness_metrics import write_readiness_report

def main():
    data=write_readiness_report(ROOT, ROOT/'results'/'repository_readiness_metrics.json')
    data['status']='PASS' if data['weighted_score'] >= 95 and not data['blockers'] else 'FAIL'
    print(json.dumps(data, indent=2, sort_keys=True))
    if data['status']!='PASS': raise SystemExit(1)
if __name__=='__main__': main()
