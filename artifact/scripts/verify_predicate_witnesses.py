#!/usr/bin/env python3
"""Standalone executable-predicate verifier for LatticeGuard.

The full evaluator now computes candidate status through run_full_evaluation's
predicate engine.  This verifier independently replays that predicate engine over
all generated candidates and checks the emitted predicate_evaluations.csv ledger.
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_full_evaluation as lg  # type: ignore

RESULTS = ROOT / "results"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ledger_path = RESULTS / "predicate_evaluations.csv"
    if not ledger_path.exists():
        print(json.dumps({"status": "FAIL", "error": "predicate_evaluations.csv missing; run run_full_evaluation.py first"}, indent=2))
        return 1
    subjects = lg.build_subjects()
    raw = lg.raw_candidates(subjects)
    ledger = {r["candidate_id"]: r for r in read_csv(ledger_path)}
    errors = []
    for c in raw:
        outcome = lg.predicate_outcome(c)
        row = ledger.get(c.candidate_id)
        if row is None:
            errors.append(f"missing candidate {c.candidate_id}")
            continue
        if row.get("computed_status") != outcome.status:
            errors.append(f"status mismatch {c.candidate_id}: {row.get('computed_status')} != {outcome.status}")
        if row.get("witness_hash") != lg.sha256_text(lg.stable_json(outcome.witness)):
            errors.append(f"witness mismatch {c.candidate_id}")
    status_counts = {}
    for row in ledger.values():
        status_counts[row["computed_status"]] = status_counts.get(row["computed_status"], 0) + 1
    out = {"status": "FAIL" if errors else "PASS", "errors": errors, "candidates_checked": len(raw), "ledger_rows": len(ledger), "status_counts": status_counts}
    print(json.dumps(out, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
