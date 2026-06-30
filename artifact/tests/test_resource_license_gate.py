from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.resource_license_gate import build_resource_license_gate
rows, report = build_resource_license_gate(ROOT)
assert report["status"] == "PASS", report
assert report["dependency_license_rows"] == 6
assert report["external_resource_rows"] >= 20
assert report["failures"] == 0
assert all(r["status"] == "PASS" for r in rows)
print("resource_license_gate PASS")
