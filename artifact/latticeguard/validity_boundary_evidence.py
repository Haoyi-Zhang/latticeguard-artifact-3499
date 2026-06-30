from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _pct(num: int, den: int) -> str:
    if den == 0:
        return "0.00"
    return f"{(num / den) * 100:.2f}"


def _mutant_operator(row: dict[str, str]) -> str:
    version = row.get("adapter_version", "")
    if "::" in version:
        return version.rsplit("::", 1)[-1]
    adapter = row.get("adapter_id", "")
    marker = "_mutant_"
    if marker in adapter:
        return adapter.split(marker, 1)[-1]
    return adapter or "unknown"


def build_validity_boundary_evidence(root: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    results = root / "results"
    summary = _read_json(results / "summary.json")
    obligations = _read_csv(results / "obligations.csv")
    rejections = _read_csv(results / "rejections.csv")
    mutants = _read_csv(results / "mutant_obligations.csv")
    overfit = _read_csv(results / "overfitting_audit.csv")
    source_gate = _read_csv(results / "source_provenance_gate.csv")
    validity = _read_json(results / "validity_challenge_evidence.json")

    breakdown: list[dict[str, Any]] = []
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in obligations:
        groups[(row.get("relation_id", ""), row.get("adapter_id", ""))].append(row)
    for relation_id, adapter_id in sorted(groups):
        rows = groups[(relation_id, adapter_id)]
        applicable = [r for r in rows if r.get("applicability_status") == "APPLICABLE_EVALUATED"]
        rejected = [r for r in rows if r.get("applicability_status") == "REJECTED_NOT_COUNTED"]
        unsupported = [r for r in rows if r.get("applicability_status") == "UNSUPPORTED_NOT_COUNTED"]
        passed = [r for r in applicable if r.get("oracle_status") == "PASS"]
        failed = [r for r in applicable if r.get("oracle_status") == "FAIL"]
        all_candidates = len(rows)
        breakdown.append({
            "relation_id": relation_id,
            "adapter_id": adapter_id,
            "generated_candidates": all_candidates,
            "applicable_evaluated": len(applicable),
            "rejected_not_counted": len(rejected),
            "unsupported_not_counted": len(unsupported),
            "passes": len(passed),
            "failures": len(failed),
            "primary_pass_rate": _pct(len(passed), len(applicable)),
            "all_candidates_as_denominator_pass_rate": _pct(len(passed), all_candidates),
            "accounting_rule": "only rows admitted by law-specific applicability and support predicates enter the primary denominator",
        })

    rejection_examples: list[dict[str, Any]] = []
    seen_reasons: set[tuple[str, str]] = set()
    for row in sorted(rejections, key=lambda r: (r.get("relation_id", ""), r.get("reason_code", ""), r.get("candidate_id", ""))):
        key = (row.get("relation_id", ""), row.get("reason_code", ""))
        if key in seen_reasons:
            continue
        seen_reasons.add(key)
        rejection_examples.append({
            "relation_id": row.get("relation_id", ""),
            "reason_code": row.get("reason_code", ""),
            "candidate_family": row.get("candidate_id", "").split(":", 1)[-1],
            "would_be_unsound_if_counted": row.get("would_be_unsound_if_counted", ""),
            "predicate_id": row.get("predicate_id", ""),
        })
        if len(rejection_examples) >= 12:
            break

    mutant_groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in mutants:
        mutant_groups[(_mutant_operator(row), row.get("relation_id", ""))].append(row)
    mutant_sensitivity: list[dict[str, Any]] = []
    for operator, relation_id in sorted(mutant_groups):
        rows = mutant_groups[(operator, relation_id)]
        killed = [r for r in rows if str(r.get("killed", "")).lower() == "true"]
        mutant_sensitivity.append({
            "seeded_operator": operator,
            "relation_id": relation_id,
            "seeded_rows": len(rows),
            "killed_rows": len(killed),
            "kill_rate_percent": _pct(len(killed), len(rows)),
            "interpretation": "positive-control sensitivity for law violations, not a discovered-vulnerability rate",
        })

    source_boundary: list[dict[str, Any]] = []
    holdout_by_stratum: Counter[str] = Counter()
    evaluated_by_stratum: Counter[str] = Counter()
    for row in overfit:
        kind = row.get("source_manifest_kind", "")
        stratum = kind.split(":", 1)[0] if ":" in kind else kind
        if row.get("split") == "holdout":
            holdout_by_stratum[stratum] += 1
        evaluated_by_stratum[stratum] += int(row.get("evaluated_obligations", "0") or 0)
    for row in source_gate:
        stratum = row.get("stratum", "")
        source_boundary.append({
            "stratum": stratum,
            "source_count": row.get("source_count", ""),
            "holdout_sources": holdout_by_stratum.get(stratum, 0),
            "evaluated_obligations": evaluated_by_stratum.get(stratum, 0),
            "paper_interpretation": row.get("paper_interpretation", ""),
            "claim_safety_rule": row.get("claim_safety_rule", ""),
        })

    total_generated = len(obligations)
    total_applicable = sum(1 for r in obligations if r.get("applicability_status") == "APPLICABLE_EVALUATED")
    total_rejected = sum(1 for r in obligations if r.get("applicability_status") == "REJECTED_NOT_COUNTED")
    total_unsupported = sum(1 for r in obligations if r.get("applicability_status") == "UNSUPPORTED_NOT_COUNTED")
    total_passes = sum(1 for r in obligations if r.get("oracle_status") == "PASS")
    total_failures = sum(1 for r in obligations if r.get("oracle_status") == "FAIL")
    total_mutants = len(mutants)
    total_killed = sum(1 for r in mutants if str(r.get("killed", "")).lower() == "true")
    killed_relations = sorted({r.get("relation_id", "") for r in mutants if str(r.get("killed", "")).lower() == "true"})
    killed_operators = sorted({_mutant_operator(r) for r in mutants if str(r.get("killed", "")).lower() == "true"})

    checks = [
        ("VB_001", total_generated == total_applicable + total_rejected + total_unsupported, "candidate outcome classes partition the generated obligation surface"),
        ("VB_002", total_applicable == int(summary.get("primary_evaluated_obligations", -1)), "applicable rows match the primary denominator"),
        ("VB_003", total_rejected == int(summary.get("rejected_invalid_transformations", -1)), "rejected rows remain visible outside the denominator"),
        ("VB_004", total_unsupported == int(summary.get("unsupported_transformations", -1)), "unsupported fragments remain visible outside the denominator"),
        ("VB_005", total_failures == int(summary.get("primary_real_failures", -1)), "primary failures are computed only after applicability and support admission"),
        ("VB_006", len(rejection_examples) >= 5, "representative rejection reasons are available for inspection"),
        ("VB_007", total_mutants == int(summary.get("seeded_mutant_rows", -1)), "seeded positive-control rows match the frozen summary"),
        ("VB_008", total_killed == int(summary.get("seeded_mutants_killed", -1)), "seeded positive-control kills match the frozen summary"),
        ("VB_009", len(killed_relations) >= 3 and len(killed_operators) >= 3, "failure sensitivity is spread across more than one law family and drift operator"),
        ("VB_010", validity.get("opa_native_closure_claimed") is False, "OPA/Rego hierarchy evidence is bounded to the normalized-decision fragment"),
        ("VB_011", int(validity.get("holdout_evaluated_obligations", 0)) >= 5000, "outcome-independent holdout contains enough evaluated obligations for an audit surface"),
        ("VB_012", int(validity.get("holdout_relation_count", 0)) == 12, "holdout covers all relation families"),
        ("VB_013", int(validity.get("holdout_adapter_count", 0)) == 3, "holdout covers all counted adapters"),
        ("VB_014", any(r.get("stratum") == "semantic_stress_witness" and "not as independent" in r.get("claim_safety_rule", "") for r in source_gate), "stress witnesses carry an explicit non-prevalence claim boundary"),
    ]
    check_rows = [{"check_id": cid, "status": "PASS" if passed else "FAIL", "rule": rule} for cid, passed, rule in checks]
    failures = [row for row in check_rows if row["status"] != "PASS"]
    report = {
        "status": "PASS" if not failures else "FAIL",
        "checks": len(check_rows),
        "failures": len(failures),
        "failure_ids": [row["check_id"] for row in failures],
        "generated_candidates": total_generated,
        "primary_evaluated_obligations": total_applicable,
        "rejected_invalid_transformations": total_rejected,
        "unsupported_transformations": total_unsupported,
        "all_candidates_as_denominator_pass_rate": _pct(total_passes, total_generated),
        "primary_pass_rate": _pct(total_passes, total_applicable),
        "seeded_rows": total_mutants,
        "seeded_killed_rows": total_killed,
        "seeded_kill_rate_percent": _pct(total_killed, total_mutants),
        "seeded_killed_relations": ";".join(killed_relations),
        "seeded_killed_operators": ";".join(killed_operators),
        "holdout_evaluated_obligations": int(validity.get("holdout_evaluated_obligations", 0)),
        "opa_normalized_decision_rows": int(validity.get("opa_normalized_decision_rows", 0)),
        "opa_native_closure_claimed": validity.get("opa_native_closure_claimed"),
        "interpretation": "Primary zero-failure evidence is bounded by explicit denominator accounting, normalized-fragment scope, holdout replay, and seeded positive controls.",
    }
    tables = {
        "validity_boundary_evidence": check_rows,
        "applicability_breakdown": breakdown,
        "rejection_examples": rejection_examples,
        "seeded_drift_sensitivity": mutant_sensitivity,
        "source_boundary_summary": source_boundary,
    }
    return tables, report


def write_validity_boundary_evidence(root: Path) -> dict[str, Any]:
    tables, report = build_validity_boundary_evidence(root)
    results = root / "results"
    _write_csv(results / "validity_boundary_evidence.csv", tables["validity_boundary_evidence"], ["check_id", "status", "rule"])
    _write_csv(results / "applicability_breakdown.csv", tables["applicability_breakdown"], [
        "relation_id", "adapter_id", "generated_candidates", "applicable_evaluated",
        "rejected_not_counted", "unsupported_not_counted", "passes", "failures",
        "primary_pass_rate", "all_candidates_as_denominator_pass_rate", "accounting_rule",
    ])
    _write_csv(results / "rejection_examples.csv", tables["rejection_examples"], [
        "relation_id", "reason_code", "candidate_family", "would_be_unsound_if_counted", "predicate_id",
    ])
    _write_csv(results / "seeded_drift_sensitivity.csv", tables["seeded_drift_sensitivity"], [
        "seeded_operator", "relation_id", "seeded_rows", "killed_rows", "kill_rate_percent", "interpretation",
    ])
    _write_csv(results / "source_boundary_summary.csv", tables["source_boundary_summary"], [
        "stratum", "source_count", "holdout_sources", "evaluated_obligations", "paper_interpretation", "claim_safety_rule",
    ])
    _write_json(results / "validity_boundary_evidence.json", report)
    return report
