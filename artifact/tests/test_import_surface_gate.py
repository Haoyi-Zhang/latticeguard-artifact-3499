from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.import_surface_gate import build_import_surface_gate
rows, report = build_import_surface_gate(ROOT)
assert report["status"] == "PASS", report
assert report["scanned_python_files"] >= 100
assert report["import_rows"] >= report["scanned_python_files"]
assert not report["undeclared_external_imports"]
print("import_surface_gate PASS")
