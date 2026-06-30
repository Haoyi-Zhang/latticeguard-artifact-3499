from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.open_science_compliance_gate import build_open_science_compliance_gate

rows, report = build_open_science_compliance_gate(ROOT)
assert report["status"] == "PASS", report
assert report["open_science_checks"] >= 6
assert all(row["status"] == "PASS" for row in rows)
