from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.dependency_provenance_gate import build_dependency_provenance_gate
rows, report = build_dependency_provenance_gate(ROOT)
assert report["status"] == "PASS", report
assert report["pinned_dependencies"] == 6
assert all(r["status"] == "PASS" for r in rows)
print("dependency_provenance_gate PASS")
