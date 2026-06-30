#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.artifact_depth import compute_depth
out=compute_depth(ROOT)
(ROOT/'results'/'artifact_depth.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
print(json.dumps(out, indent=2, sort_keys=True))
if out['status']!='PASS': raise SystemExit(1)
