from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.narrative_claim_scan_gate import build_narrative_claim_scan_gate
rows, report = build_narrative_claim_scan_gate(ROOT)
assert report["status"] == "PASS", report
assert report["narrative_claim_rows"] >= 12
print("narrative_claim_scan_gate PASS")
