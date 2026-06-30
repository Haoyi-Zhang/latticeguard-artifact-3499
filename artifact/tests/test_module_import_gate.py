from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.module_import_gate import build_module_import_gate
rows, report = build_module_import_gate(ROOT)
assert report["status"] == "PASS", report
assert report["compiled_files"] >= 100
assert report["imported_modules"] >= 50
print("module_import_gate PASS")
