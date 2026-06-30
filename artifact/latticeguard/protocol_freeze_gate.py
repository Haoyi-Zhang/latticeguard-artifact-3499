from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _empty(row: dict[str, str], keys: Iterable[str]) -> bool:
    return all(str(row.get(key, "")).strip() == "" for key in keys)


def _status(value: bool) -> str:
    return "PASS" if value else "FAIL"


def _block(source: str, start: str, end: str) -> str:
    begin = source.find(start)
    if begin < 0:
        return ""
    finish = source.find(end, begin + len(start))
    if finish < 0:
        finish = len(source)
    return source[begin:finish]


def protocol_freeze_rows(root: Path) -> list[dict[str, str]]:
    results = root / "results"
    contracts = _rows(results / "relation_contracts.csv")
    obligations = _rows(results / "obligations.csv")
    predicates = _rows(results / "predicate_evaluations.csv")
    deployed = _read_json(results / "deployed_tool_crosswalk.json")
    provenance = _read_json(results / "source_provenance_gate.json")
    denominator = _read_json(results / "denominator_integrity_gate.json")
    overfit = _read_json(results / "overfitting_audit.json")
    source_text = (root / "scripts" / "run_full_evaluation.py").read_text(encoding="utf-8")

    relation_keys = {
        "relation_id",
        "law_name",
        "applicability_predicate_id",
        "transformation",
        "expected_invariant",
        "invalid_transformation_rejection",
        "minimization_criterion",
    }
    contract_ok = len(contracts) == 12 and all(relation_keys <= set(row) and all(row.get(k, "").strip() for k in relation_keys) for row in contracts)

    predicate_ids = {row.get("candidate_id", "") for row in predicates}
    obligation_ids = {row.get("candidate_id", "") for row in obligations}
    predicate_ok = bool(predicate_ids) and obligation_ids <= predicate_ids and all(
        row.get("computed_status", "").strip()
        and (row.get("predicate_witness_hash", "").strip() or row.get("witness_hash", "").strip())
        for row in predicates
    )

    decision_fields = ["before_decision", "after_decision", "before_raw_decision", "after_raw_decision"]
    excluded = [row for row in obligations if row.get("applicability_status") != "APPLICABLE_EVALUATED"]
    excluded_ok = bool(excluded) and all(_empty(row, decision_fields) for row in excluded)

    counted = [row for row in obligations if row.get("applicability_status") == "APPLICABLE_EVALUATED"]
    counted_ok = bool(counted) and all(
        row.get("predicate_inputs_hash", "").strip()
        and row.get("predicate_witness_hash", "").strip()
        and not _empty(row, decision_fields)
        and row.get("oracle_status") in {"PASS", "FAIL"}
        for row in counted
    )

    holdout_ok = (
        overfit.get("status") == "PASS"
        and "sha256" in str(overfit.get("source_split_rule", "")).lower()
        and int(overfit.get("holdout_obligations", overfit.get("holdout_evaluated_obligations", 0))) >= 5000
        and int(overfit.get("holdout_relation_count", 0)) == 12
        and int(overfit.get("holdout_adapter_count", 0)) >= 3
    )

    denominator_ok = denominator.get("status") == "PASS" and int(denominator.get("failures", 1)) == 0

    admission_block = _block(source_text, "def all_candidates", "class AdapterBase")
    order_terms = [
        admission_block.find("trusted = [apply_predicate_engine"),
        admission_block.find("counted = sorted"),
        admission_block.find("rejected = sorted"),
    ]
    order_ok = all(pos >= 0 for pos in order_terms) and order_terms == sorted(order_terms)

    predicate_block = _block(source_text, "def predicate_outcome", "def apply_predicate_engine")
    forbidden_result_terms = [
        "RESULTS",
        "baseline_results",
        "obligations.csv",
        "oracle_status",
        ".decide(",
        "Decision(",
    ]
    predicate_isolation_ok = bool(predicate_block) and not any(term in predicate_block for term in forbidden_result_terms)

    provenance_ok = (
        provenance.get("status") == "PASS"
        and int(provenance.get("audited_subject_sources", provenance.get("classified_sources", 0))) >= 100
        and int(provenance.get("semantic_stress_witness_sources", 0)) >= 90
    )

    crosswalk_ok = (
        deployed.get("status") == "PASS"
        and int(deployed.get("rows", 0)) >= 8
        and deployed.get("only_full_oracle_has_all_features") is True
        and deployed.get("release_pair_bug_claimed") is False
    )
    rejected_predicates = [row for row in predicates if row.get("computed_status") != "APPLICABLE_EVALUATED"]
    label_recompute_ok = (
        bool(predicates)
        and "generator_status_before_predicate" in predicates[0]
        and "computed_status" in predicates[0]
        and "out = predicate_outcome(c)" in source_text
        and len(rejected_predicates) >= 1000
    )

    checks = [
        ("PF_001", "relation contracts are explicit and complete before execution", f"contracts={len(contracts)}", contract_ok),
        ("PF_002", "predicate witness ledger covers all candidate ids", f"predicates={len(predicate_ids)} obligations={len(obligation_ids)}", predicate_ok),
        ("PF_003", "excluded rows retain no adapter outcomes", f"excluded={len(excluded)}", excluded_ok),
        ("PF_004", "counted rows carry predicate hashes and adapter outcomes", f"counted={len(counted)}", counted_ok),
        ("PF_005", "holdout split is hash-based and covers all relation families", f"rule={overfit.get('source_split_rule', '')}", holdout_ok),
        ("PF_006", "denominator-integrity gate is closed", f"status={denominator.get('status', '')}", denominator_ok),
        ("PF_007", "candidate admission is computed before counted/rejected aggregation", "all_candidates ordering", order_ok),
        ("PF_008", "predicate block does not read generated result ledgers or adapter outcomes", "predicate_outcome static scan", predicate_isolation_ok),
        ("PF_009", "source provenance separates upstream, native, stress, and generated strata", f"sources={provenance.get('audited_subject_sources', provenance.get('classified_sources', 0))}", provenance_ok),
        ("PF_010", "deployed-tool comparison is a bounded nearest-neighbor crosswalk", f"rows={deployed.get('rows', 0)}", crosswalk_ok),
        ("PF_011", "predicate status is recomputed rather than trusting generator labels", f"rejected_predicates={len(rejected_predicates)}", label_recompute_ok),
    ]
    return [
        {
            "check_id": check_id,
            "rule": rule,
            "observed": observed,
            "status": _status(ok),
        }
        for check_id, rule, observed, ok in checks
    ]


def write_protocol_freeze_gate(root: Path) -> dict[str, object]:
    rows = protocol_freeze_rows(root)
    result_dir = root / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    with (result_dir / "protocol_freeze_gate.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check_id", "rule", "observed", "status"])
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["status"] != "PASS"]
    report = {
        "status": "PASS" if not failures else "FAIL",
        "checks": len(rows),
        "failures": len(failures),
        "failed_checks": [row["check_id"] for row in failures],
    }
    (result_dir / "protocol_freeze_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
