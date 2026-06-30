from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists(): return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists(): return {}
    return json.loads(path.read_text(encoding="utf-8"))

def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)

def build_denominator_integrity_gate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    res = root / "results"
    summary = _read_json(res / "summary.json")
    obligations = _read_csv(res / "obligations.csv")
    rejections = _read_csv(res / "rejections.csv")
    coverage = _read_csv(res / "coverage.csv")
    baseline = _read_csv(res / "baseline_results.csv")
    mutants = _read_csv(res / "mutant_obligations.csv")
    adapter_exclusions = _read_csv(res / "adapter_exclusions.csv")
    subject_exclusions = _read_csv(res / "subject_exclusions.csv")
    applicable = [r for r in obligations if r.get("applicability_status") == "APPLICABLE_EVALUATED"]
    rejected = [r for r in obligations if r.get("applicability_status") == "REJECTED_NOT_COUNTED"]
    unsupported = [r for r in obligations if r.get("applicability_status") == "UNSUPPORTED_NOT_COUNTED"]
    rows: list[dict[str, Any]] = []
    def add(check_id: str, condition: bool, observed: Any, expected: Any, rule: str) -> None:
        rows.append({"check_id": check_id, "status": "PASS" if condition else "FAIL", "observed": observed, "expected": expected, "rule": rule})
    add("DEN_001", len(applicable) == int(summary.get("primary_evaluated_obligations", -1)), len(applicable), summary.get("primary_evaluated_obligations"), "only APPLICABLE_EVALUATED rows enter primary denominator")
    add("DEN_002", sum(1 for r in applicable if r.get("oracle_status") == "PASS") == int(summary.get("primary_passes", -1)), sum(1 for r in applicable if r.get("oracle_status") == "PASS"), summary.get("primary_passes"), "primary pass count is computed only over applicable rows")
    add("DEN_003", sum(1 for r in applicable if r.get("oracle_status") == "FAIL") == int(summary.get("primary_real_failures", -1)), sum(1 for r in applicable if r.get("oracle_status") == "FAIL"), summary.get("primary_real_failures"), "primary failure count is computed only over applicable rows")
    add("DEN_004", len(rejected) == int(summary.get("rejected_invalid_transformations", -1)), len(rejected), summary.get("rejected_invalid_transformations"), "invalid transformations are rejected before denominator accounting")
    add("DEN_005", len(unsupported) == int(summary.get("unsupported_transformations", -1)), len(unsupported), summary.get("unsupported_transformations"), "unsupported fragments remain outside primary pass/fail accounting")
    add("DEN_006", all(r.get("oracle_status") == "PASS" for r in applicable), sum(1 for r in applicable if r.get("oracle_status") != "PASS"), 0, "all counted rows must have PASS in this artifact run")
    add("DEN_007", all(r.get("oracle_status") in {"REJECTED_NOT_COUNTED","UNSUPPORTED_NOT_COUNTED"} for r in rejected + unsupported), sorted({r.get("oracle_status") for r in rejected + unsupported}), "not counted statuses only", "rejected/unsupported rows cannot masquerade as PASS")
    rejection_ids = {r.get("candidate_id") for r in rejections}
    rejected_ids = {r.get("candidate_id") for r in rejected}
    add("DEN_008", rejection_ids <= rejected_ids and rejected_ids <= rejection_ids, f"ledger={len(rejection_ids)};obligation={len(rejected_ids)}", "equal candidate-id sets", "rejections.csv and obligations rejected rows agree by candidate id")
    adapters = sorted({r.get("adapter_id") for r in applicable})
    expected_adapters = sorted(str(summary.get("executed_adapter_ids", "")).split(";"))
    expected_adapters = [a for a in expected_adapters if a]
    add("DEN_009", adapters == expected_adapters, ";".join(adapters), ";".join(expected_adapters), "counted adapter set must match the hash-gated execution manifest")
    add("DEN_010", not any(r.get("oracle_status") in {"ERROR","TIMEOUT"} for r in applicable), sum(1 for r in applicable if r.get("oracle_status") in {"ERROR","TIMEOUT"}), 0, "error/timeout rows cannot enter primary denominator")
    coverage_passes = sum(int(r.get("pass_count", "0") or 0) for r in coverage)
    add("DEN_011", coverage_passes == int(summary.get("primary_passes", -1)), coverage_passes, summary.get("primary_passes"), "coverage pass totals match primary pass count")
    primary_row_ids = {r.get("row_id") for r in obligations}
    baseline_ids = {r.get("row_id") for r in baseline} | {r.get("row_id") for r in mutants}
    add("DEN_012", primary_row_ids.isdisjoint(baseline_ids), len(primary_row_ids & baseline_ids), 0, "baseline/seeded controls cannot share primary row ids")
    excluded_sources = {r.get("source_id") for r in subject_exclusions}
    primary_sources = {r.get("source_id") for r in obligations}
    add("DEN_013", excluded_sources.isdisjoint(primary_sources), len(excluded_sources & primary_sources), 0, "subject exclusions cannot appear in primary obligation rows")
    pre_excl = [r for r in adapter_exclusions if r.get("adapter_id") == "opa_rego_cli"]
    opa_counted = "opa_rego_cli" in expected_adapters
    if opa_counted:
        add("DEN_014", not pre_excl, len(pre_excl), "0 because hash-gated OPA is counted", "OPA is either hash-gated into the denominator or excluded before results")
    else:
        add("DEN_014", bool(pre_excl) and all(r.get("results_observed_before_exclusion") == "false" for r in pre_excl), len(pre_excl), ">=1 pre-result OPA exclusion", "OPA is either hash-gated into the denominator or excluded before results")
    failures=[r for r in rows if r["status"] != "PASS"]
    report={"status":"PASS" if not failures else "FAIL", "checks":len(rows), "failures":len(failures), "failure_ids":[r["check_id"] for r in failures]}
    return rows, report

def write_denominator_integrity_gate(root: Path) -> dict[str, Any]:
    rows, report = build_denominator_integrity_gate(root)
    _write_csv(root / "results" / "denominator_integrity_gate.csv", rows, ["check_id","status","observed","expected","rule"])
    (root / "results" / "denominator_integrity_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
