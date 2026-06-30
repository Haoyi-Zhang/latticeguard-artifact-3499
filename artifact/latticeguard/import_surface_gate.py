from __future__ import annotations
import ast
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT_PACKAGE = "latticeguard"
ALLOWED_VENDOR_IMPORTS = {"casbin", "cedarpy", "simpleeval", "wcmatch", "bracex", "pypdf"}
ALLOWED_LOCAL_ALIASES = {"law_algebra", "evidence_queries", "repo_quality", "scripts"}
SOURCE_DIRS = ("latticeguard", "scripts", "tests")


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                found.add(node.module.split(".", 1)[0])
    return found


def _declared_vendor_roots(root: Path) -> set[str]:
    declared = set(ALLOWED_VENDOR_IMPORTS)
    requirements = root / "requirements.txt"
    if requirements.exists():
        for line in requirements.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = line.split("==", 1)[0].lower().replace("_", "-")
            if name == "pycasbin":
                declared.add("casbin")
            elif name in {"cedarpy", "simpleeval", "wcmatch", "bracex", "pypdf"}:
                declared.add(name.replace("-", "_"))
    return declared


def build_import_surface_gate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    stdlib = set(sys.stdlib_module_names)
    vendor_roots = _declared_vendor_roots(root)
    script_stems = {p.stem for p in (root / "scripts").glob("*.py")}
    test_stems = {p.stem for p in (root / "tests").glob("test_*.py")}
    allowed = stdlib | vendor_roots | {ROOT_PACKAGE} | ALLOWED_LOCAL_ALIASES | script_stems | test_stems
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    scanned = 0
    for dirname in SOURCE_DIRS:
        for path in sorted((root / dirname).glob("*.py" if dirname != "tests" else "test_*.py")):
            scanned += 1
            rel = path.relative_to(root).as_posix()
            try:
                imports = _top_level_imports(path)
            except Exception as exc:
                rows.append({"path": rel, "import_name": "<parse>", "classification": "parse_error", "status": "FAIL", "detail": f"{type(exc).__name__}:{exc}"})
                failures.append(rel)
                continue
            if not imports:
                rows.append({"path": rel, "import_name": "<none>", "classification": "no_imports", "status": "PASS", "detail": ""})
                continue
            for name in sorted(imports):
                if name in stdlib:
                    classification = "stdlib"
                elif name in vendor_roots:
                    classification = "declared_vendored_dependency"
                elif name == ROOT_PACKAGE or name in ALLOWED_LOCAL_ALIASES or name in script_stems or name in test_stems:
                    classification = "local"
                else:
                    classification = "undeclared_external"
                status = "PASS" if name in allowed else "FAIL"
                if status != "PASS":
                    failures.append(f"{rel}:{name}")
                rows.append({"path": rel, "import_name": name, "classification": classification, "status": status, "detail": ""})
    report = {
        "status": "PASS" if not failures else "FAIL",
        "scanned_python_files": scanned,
        "import_rows": len(rows),
        "declared_vendor_import_roots": sorted(vendor_roots),
        "undeclared_external_imports": failures,
    }
    return rows, report


def write_import_surface_gate(root: Path) -> dict[str, Any]:
    rows, report = build_import_surface_gate(root)
    _write_csv(root / "results" / "import_surface_gate.csv", rows, ["path", "import_name", "classification", "status", "detail"])
    (root / "results" / "import_surface_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
