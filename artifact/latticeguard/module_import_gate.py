from __future__ import annotations
import csv, importlib, json, sys, shutil
from pathlib import Path
from typing import Any


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)

def build_module_import_gate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sys.dont_write_bytecode = True
    for p in [root / "vendor_python", root]:
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    rows: list[dict[str, Any]] = []
    compile_failures: list[str] = []
    import_failures: list[str] = []
    py_files = sorted(list((root / "latticeguard").glob("*.py")) + list((root / "scripts").glob("*.py")) + list((root / "tests").glob("test_*.py")))
    for path in py_files:
        rel = path.relative_to(root).as_posix()
        status = "PASS"
        detail = "compiled"
        try:
            compile(path.read_text(encoding="utf-8"), rel, "exec")
        except Exception as exc:
            status = "FAIL"; detail = f"compile:{type(exc).__name__}:{exc}"; compile_failures.append(rel)
        rows.append({"path": rel, "check": "compile", "status": status, "detail": detail})
    for path in sorted((root / "latticeguard").glob("*.py")):
        if path.name == "__init__.py":
            continue
        module = "latticeguard." + path.stem
        status = "PASS"; detail = "imported"
        try:
            importlib.import_module(module)
        except Exception as exc:
            status = "FAIL"; detail = f"import:{type(exc).__name__}:{exc}"; import_failures.append(module)
        rows.append({"path": module, "check": "import", "status": status, "detail": detail})
    pycache = root / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache, ignore_errors=True)
    for p in root.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
    report = {"status": "PASS" if not compile_failures and not import_failures else "FAIL", "compiled_files": len(py_files), "imported_modules": len(list((root / "latticeguard").glob("*.py"))) - 1, "compile_failures": compile_failures, "import_failures": import_failures}
    return rows, report

def write_module_import_gate(root: Path) -> dict[str, Any]:
    rows, report = build_module_import_gate(root)
    _write_csv(root / "results" / "module_import_gate.csv", rows, ["path","check","status","detail"])
    (root / "results" / "module_import_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
