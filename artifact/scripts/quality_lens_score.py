#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.artifact_depth import compute_depth
from latticeguard.audit_score import grade

def main() -> None:
    metrics=compute_depth(ROOT)
    out=grade(metrics)
    out["metrics"]=metrics
    out["gate"]="quality_lens_score"
    (ROOT/"results"/"quality_lens_score.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    if out.get("status") != "PASS":
        raise SystemExit(1)
if __name__=="__main__": main()
