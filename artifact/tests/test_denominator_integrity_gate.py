from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.denominator_integrity_gate import build_denominator_integrity_gate
rows, report = build_denominator_integrity_gate(ROOT)
assert report["status"] == "PASS", report
assert report["checks"] >= 14
assert all(r["status"] == "PASS" for r in rows)
print("denominator_integrity_gate PASS")
