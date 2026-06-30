from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.content_residue_gate import build_content_residue_gate
rows, report = build_content_residue_gate(ROOT)
assert report["status"] == "PASS", (report, rows[:5])
assert report["scanned_files"] >= 100
print("content_residue_gate PASS")
