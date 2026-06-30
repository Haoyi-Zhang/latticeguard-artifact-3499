#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.minimization_replay import replay_all_counterexamples

def main() -> None:
    report=replay_all_counterexamples(ROOT)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report['status']!='PASS': raise SystemExit(1)
if __name__=='__main__': main()
