from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.venue_requirements import build_venue_requirements
rows, report = build_venue_requirements(ROOT)
assert report["status"] == "PASS", report
assert len(rows) >= 10
assert min(int(r["score"]) for r in rows) >= 95
print("venue_requirements PASS")
