from __future__ import annotations
import csv, importlib, json, sys
from pathlib import Path
from typing import Any

PINNED_IMPORTS = {
    "pycasbin": "casbin",
    "cedarpy": "cedarpy",
    "simpleeval": "simpleeval",
    "wcmatch": "wcmatch",
    "bracex": "bracex",
    "pypdf": "pypdf",
}

def _read_pins(root: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in (root / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            name, version = line.split("==", 1)
            pins[name.strip().lower()] = version.strip()
    return pins

def _metadata(root: Path, name: str, version: str) -> tuple[Path | None, dict[str, str]]:
    vendor = root / "vendor_python"
    candidates = list(vendor.glob(f"{name}-{version}.dist-info/METADATA"))
    if not candidates and name == "pycasbin":
        candidates = list(vendor.glob(f"pycasbin-{version}.dist-info/METADATA"))
    if not candidates:
        return None, {}
    fields: dict[str, str] = {}
    license_classifiers: list[str] = []
    for line in candidates[0].read_text(encoding="utf-8", errors="ignore").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip(); v = v.strip()
            if k in {"Name", "Version", "License", "License-Expression", "License-File", "Summary", "Home-page"}:
                fields[k] = v
            if k == "Classifier" and "License ::" in v:
                license_classifiers.append(v)
    if not fields.get("License") and fields.get("License-Expression"):
        fields["License"] = fields["License-Expression"]
    if not fields.get("License"):
        for classifier in license_classifiers:
            if "MIT License" in classifier:
                fields["License"] = "MIT"
                break
            if "Apache Software License" in classifier:
                fields["License"] = "Apache-2.0"
                break
    if not fields.get("License"):
        license_dir = candidates[0].parent / "licenses"
        text = ""
        if license_dir.exists():
            for lf in sorted(license_dir.glob("*")):
                if lf.is_file():
                    text += lf.read_text(encoding="utf-8", errors="ignore")[:2000].lower()
        if "apache license" in text and "version 2.0" in text:
            fields["License"] = "Apache-2.0"
        elif "mit license" in text or "mit licence" in text:
            fields["License"] = "MIT"
    return candidates[0], fields

def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)

def build_dependency_provenance_gate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pins = _read_pins(root)
    vendor = root / "vendor_python"
    if str(vendor) not in sys.path:
        sys.path.insert(0, str(vendor))
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for dep in sorted(PINNED_IMPORTS):
        pinned = pins.get(dep, "")
        meta_path, fields = _metadata(root, dep, pinned)
        import_name = PINNED_IMPORTS[dep]
        import_path = ""
        import_ok = False
        try:
            cached = sys.modules.get(import_name)
            if cached is not None:
                cached_path = str(Path(getattr(cached, "__file__", "")).resolve())
                if str(vendor.resolve()) not in cached_path:
                    sys.modules.pop(import_name, None)
            mod = importlib.import_module(import_name)
            import_path = str(Path(getattr(mod, "__file__", "")).resolve())
            import_ok = str(vendor.resolve()) in import_path
        except Exception as exc:  # pragma: no cover - report path
            import_path = f"IMPORT_ERROR:{type(exc).__name__}:{exc}"
        ok = bool(pinned) and meta_path is not None and fields.get("Version") == pinned and import_ok
        if not ok:
            failures.append(dep)
        rows.append({
            "dependency": dep,
            "pinned_version": pinned,
            "metadata_name": fields.get("Name", "missing"),
            "metadata_version": fields.get("Version", "missing"),
            "license_field": fields.get("License", "not_declared_in_metadata"),
            "import_name": import_name,
            "import_resolved_to_vendor": str(import_ok).lower(),
            "metadata_path": str(meta_path.relative_to(root)) if meta_path else "missing",
            "status": "PASS" if ok else "FAIL",
        })
    report = {"status": "PASS" if not failures else "FAIL", "pinned_dependencies": len(rows), "dependency_failures": len(failures), "failure_dependencies": failures}
    return rows, report

def write_dependency_provenance_gate(root: Path) -> dict[str, Any]:
    rows, report = build_dependency_provenance_gate(root)
    _write_csv(root / "results" / "dependency_provenance_gate.csv", rows, ["dependency","pinned_version","metadata_name","metadata_version","license_field","import_name","import_resolved_to_vendor","metadata_path","status"])
    (root / "results" / "dependency_provenance_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
