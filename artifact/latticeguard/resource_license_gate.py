from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any

DEPENDENCY_IMPORTS = {
    "pycasbin": "casbin",
    "cedarpy": "cedarpy",
    "simpleeval": "simpleeval",
    "wcmatch": "wcmatch",
    "bracex": "bracex",
    "pypdf": "pypdf",
}
ALLOWED_LICENSES = {"MIT", "Apache-2.0", "Apache 2.0", "Apache Software License", "Apache License 2.0", "BSD-3-Clause"}
UNRESOLVED_MARKERS = [
    "to verify",
    "re-check",
    "recheck",
    "reconnaissance",
    "feasibility stage",
    "must be resolved",
    "current crawl",
    "latest discrepancy",
    "candidate pinned",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_pins(root: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in (root / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            name, version = line.split("==", 1)
            pins[name.strip().lower()] = version.strip()
    return pins


def _metadata_path(root: Path, dep: str, version: str) -> Path | None:
    vendor = root / "vendor_python"
    candidates = sorted(vendor.glob(f"{dep}-{version}.dist-info/METADATA"))
    if dep == "pycasbin":
        candidates.extend(sorted(vendor.glob(f"pycasbin-{version}.dist-info/METADATA")))
    return candidates[0] if candidates else None


def _metadata_fields(path: Path) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields.setdefault(key.strip(), []).append(value.strip())
    return fields


def _license_from_metadata(fields: dict[str, list[str]], license_files: list[Path]) -> str:
    for key in ("License-Expression", "License"):
        vals = [v for v in fields.get(key, []) if v]
        if vals:
            return vals[0]
    classifiers = fields.get("Classifier", [])
    for c in classifiers:
        if "Apache Software License" in c:
            return "Apache-2.0"
        if "MIT License" in c:
            return "MIT"
    for lf in license_files:
        text = lf.read_text(encoding="utf-8", errors="ignore")[:2000].lower()
        if "apache license" in text and "version 2.0" in text:
            return "Apache-2.0"
        if "mit license" in text or "mit licence" in text:
            return "MIT"
        if "bsd 3-clause" in text or "redistribution and use in source and binary forms" in text:
            return "BSD-3-Clause"
    return "UNKNOWN"


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_resource_license_gate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pins = _read_pins(root)
    vendor = root / "vendor_python"
    notice = root / "THIRD_PARTY_NOTICES.md"
    notice_text = notice.read_text(encoding="utf-8", errors="ignore") if notice.exists() else ""

    dep_failures = 0
    for dep in sorted(DEPENDENCY_IMPORTS):
        version = pins.get(dep, "")
        meta = _metadata_path(root, dep, version)
        fields: dict[str, list[str]] = _metadata_fields(meta) if meta else {}
        dist = meta.parent if meta else None
        license_files = sorted((dist / "licenses").glob("*")) if dist and (dist / "licenses").exists() else []
        license_value = _license_from_metadata(fields, [p for p in license_files if p.is_file()])
        license_hashes = ";".join(f"{p.name}:{_sha256(p)}" for p in license_files if p.is_file())
        ok = bool(version) and meta is not None and license_value in ALLOWED_LICENSES and bool(license_hashes) and dep in notice_text and version in notice_text
        if not ok:
            dep_failures += 1
        rows.append({
            "scope": "runtime_dependency",
            "resource_id": dep,
            "resource_name": dep,
            "version_or_scope": version,
            "license_disposition": license_value,
            "redistribution_status": "vendored_with_license_file",
            "evidence": f"{meta.relative_to(root) if meta else 'missing'};{license_hashes or 'missing_license_file'}",
            "status": "PASS" if ok else "FAIL",
        })

    external_rows = _read_csv(root / "external_resources.csv") if (root / "external_resources.csv").exists() else []
    external_failures = 0
    marker_re = re.compile("|".join(re.escape(m) for m in UNRESOLVED_MARKERS), re.IGNORECASE)
    for r in external_rows:
        joined = " ".join(str(v) for v in r.values())
        license_value = r.get("license", "")
        stable_scope = r.get("hash_and_freeze_plan", "")
        ok = not bool(marker_re.search(joined)) and bool(license_value) and "verify" not in license_value.lower() and bool(stable_scope)
        if not ok:
            external_failures += 1
        rows.append({
            "scope": "external_resource",
            "resource_id": r.get("resource_id", ""),
            "resource_name": r.get("resource_name", ""),
            "version_or_scope": r.get("observed_version_or_revision", ""),
            "license_disposition": license_value,
            "redistribution_status": r.get("planned_use_in_latticeguard", ""),
            "evidence": r.get("hash_and_freeze_plan", ""),
            "status": "PASS" if ok else "FAIL",
        })

    project_license_ok = "MIT License" in (root / "LICENSE").read_text(encoding="utf-8", errors="ignore")
    rows.append({
        "scope": "project_license",
        "resource_id": "latticeguard_project_license",
        "resource_name": "LatticeGuard artifact source license",
        "version_or_scope": "anonymous submission artifact",
        "license_disposition": "MIT",
        "redistribution_status": "included at artifact/LICENSE",
        "evidence": "artifact/LICENSE",
        "status": "PASS" if project_license_ok else "FAIL",
    })

    failed = [r for r in rows if r["status"] != "PASS"]
    report = {
        "status": "PASS" if not failed else "FAIL",
        "dependency_license_rows": len(DEPENDENCY_IMPORTS),
        "external_resource_rows": len(external_rows),
        "project_license_rows": 1,
        "resource_license_rows": len(rows),
        "dependency_license_failures": dep_failures,
        "external_resource_failures": external_failures,
        "failures": len(failed),
    }
    return rows, report


def write_resource_license_gate(root: Path) -> dict[str, Any]:
    rows, report = build_resource_license_gate(root)
    _write_csv(root / "results" / "resource_license_gate.csv", rows, ["scope", "resource_id", "resource_name", "version_or_scope", "license_disposition", "redistribution_status", "evidence", "status"])
    (root / "results" / "resource_license_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
