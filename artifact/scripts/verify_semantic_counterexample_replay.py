#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.semantic_counterexample_replay import write_semantic_counterexample_replay

def main() -> None:
    report=write_semantic_counterexample_replay(ROOT)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report['status']!='PASS':
        raise SystemExit(1)

if __name__=='__main__':
    main()
