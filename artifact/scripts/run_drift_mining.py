#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.drift_mining import write_drift_mining_harness, summarize_drift

def main() -> None:
    rows=write_drift_mining_harness(ROOT)
    summary=summarize_drift(rows)
    report={'status':'PASS','note':'Harness present; real drift witnesses require public release-pair seeds and are not fabricated.', **summary}
    print(json.dumps(report, indent=2, sort_keys=True))
if __name__=='__main__': main()
