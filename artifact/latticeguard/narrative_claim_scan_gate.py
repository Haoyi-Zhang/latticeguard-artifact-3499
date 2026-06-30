from __future__ import annotations
import csv
import json
import re
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _expect(rows: list[dict[str, Any]], repo: Path, rel: str, claim: str, expected: int | str, pattern: str) -> None:
    text = _text(repo / rel)
    m = re.search(pattern, text)
    observed = m.group(1) if m else "<missing>"
    status = "PASS" if str(observed) == str(expected) else "FAIL"
    line = text[:m.start()].count("\n") + 1 if m else ""
    rows.append({"path": rel, "claim": claim, "expected": expected, "observed": observed, "line": line, "status": status})


def build_narrative_claim_scan_gate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repo = root.parent
    results = root / "results"
    summary = _read_json(results / "summary.json")
    rq = _read_json(results / "research_quality_gate_matrix.json")
    delivery = _read_json(results / "reproducibility_risk_check.json")
    resource = _read_json(results / "resource_license_gate.json")
    depgate = _read_json(results / "dependency_provenance_gate.json")
    module_gate = _read_json(results / "module_import_gate.json")
    import_surface = _read_json(results / "import_surface_gate.json")
    denominator = _read_json(results / "denominator_integrity_gate.json")
    tests_count = len(list((root / "tests").glob("test_*.py")))
    rows: list[dict[str, Any]] = []

    _expect(rows, repo, "artifact/README.md", "readme_quality_lenses", rq.get("quality_lenses", ""), r"(\d+) closed research-quality gate lenses")
    _expect(rows, repo, "artifact/README.md", "readme_aggregate_checks", summary.get("aggregate_checks", ""), r"(\d+) aggregate verifier checks")
    _expect(rows, repo, "artifact/README.md", "readme_unit_tests", tests_count, r"(\d+) unit tests")
    _expect(rows, repo, "artifact/README.md", "readme_resource_rows", resource.get("resource_license_rows", ""), r"resource/license closure over (\d+) rows")

    _expect(rows, repo, "artifact/reproduction.md", "reproduction_quality_lenses", rq.get("quality_lenses", ""), r"(\d+) closed research-quality lenses")
    _expect(rows, repo, "artifact/reproduction.md", "reproduction_aggregate_checks", summary.get("aggregate_checks", ""), r"(\d+) aggregate verifier checks")
    _expect(rows, repo, "artifact/reproduction.md", "reproduction_unit_tests", tests_count, r"(\d+) unit tests")
    _expect(rows, repo, "artifact/reproduction.md", "reproduction_reproducibility_risks", delivery.get("risk_rows", ""), r"(\d+) closed reproducibility-risk rows")
    _expect(rows, repo, "artifact/reproduction.md", "reproduction_dependency_rows", depgate.get("pinned_dependencies", ""), r"(\d+) pinned dependency rows")
    _expect(rows, repo, "artifact/reproduction.md", "reproduction_denominator_checks", denominator.get("checks", ""), r"(\d+) denominator-integrity checks")
    _expect(rows, repo, "artifact/reproduction.md", "reproduction_resource_rows", resource.get("resource_license_rows", ""), r"(\d+) resource/license closure rows")
    _expect(rows, repo, "artifact/reproduction.md", "reproduction_module_import_files", module_gate.get("compiled_files", ""), r"(\d+) compiled Python files")
    _expect(rows, repo, "artifact/reproduction.md", "reproduction_import_surface_files", import_surface.get("scanned_python_files", ""), r"(\d+) scanned Python files for import-surface closure")

    failures = [r for r in rows if r["status"] != "PASS"]
    report = {
        "status": "PASS" if not failures else "FAIL",
        "narrative_claim_rows": len(rows),
        "failures": len(failures),
        "failed_claims": [r["claim"] for r in failures],
    }
    return rows, report


def write_narrative_claim_scan_gate(root: Path) -> dict[str, Any]:
    rows, report = build_narrative_claim_scan_gate(root)
    _write_csv(root / "results" / "narrative_claim_scan_gate.csv", rows, ["path", "claim", "expected", "observed", "line", "status"])
    (root / "results" / "narrative_claim_scan_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
