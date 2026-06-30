#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.theorem_ledger import write_theorem_ledgers

report = write_theorem_ledgers(ROOT)
print(json.dumps(report, indent=2, sort_keys=True))
if report.get('status') != 'PASS':
    raise SystemExit(1)
