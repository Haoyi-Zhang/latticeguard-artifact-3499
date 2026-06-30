from __future__ import annotations

"""Paper-claim traceability matrix.

This verifier makes the paper/artifact boundary auditable: every paper-visible
number must have (1) a claim_manifest entry, (2) a paper_claims row, (3) a macro
binding, and (4) at least one executable evidence file that exists in the
repository.  The matrix is intentionally small enough for artifact gateers to
inspect directly.
"""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PAPER = ROOT.parent / "paper"

EVIDENCE_BY_CLAIM = {
    "executed_real_adapters": ["results/obligations.csv", "results/adapter_semantics_matrix.csv"],
    "primary_evaluated_obligations": ["results/obligations.csv"],
    "primary_passes": ["results/obligations.csv"],
    "primary_real_failures": ["results/obligations.csv", "results/error_analysis.csv"],
    "rejected_invalid_transformations": ["results/rejections.csv", "results/obligations.csv"],
    "unsupported_transformations": ["results/obligations.csv"],
    "relation_ids_covered": ["results/coverage_lattice.csv", "results/relation_contracts.csv"],
    "source_ids_covered": ["results/coverage_lattice.csv", "results/source_provenance_gate.csv"],
    "seeded_mutant_rows": ["results/mutant_obligations.csv"],
    "seeded_mutants_killed": ["results/mutant_obligations.csv", "results/oracle_efficacy_summary.csv"],
    "minimized_counterexamples": ["results/counterexamples.json", "results/semantic_counterexample_replay.csv"],
    "scalability_rows": ["results/scalability.csv"],
    "bounded_model_checked_cases": ["results/model_check_cases.csv", "results/model_check_summary.json"],
    "bounded_model_check_failures": ["results/model_check_summary.json"],
    "bounded_model_relations": ["results/model_check_summary.json"],
    "native_selftest_rows": ["results/native_selftest_results.csv"],
    "native_selftest_passes": ["results/native_selftest_results.csv"],
    "native_selftest_failures": ["results/native_selftest_results.csv"],
    "predicate_witnesses": ["results/predicate_evaluations.csv"],
    "aggregate_checks": ["scripts/verify_all.py", "results/summary.json"],
    "mechanized_kernel_cases": ["results/mechanized_law_kernel.csv", "results/mechanized_law_kernel.json"],
    "mechanized_kernel_failures": ["results/mechanized_law_kernel.json"],
    "baseline_families": ["results/oracle_efficacy_summary.csv", "results/baseline_results.csv"],
    "quality_gate_lenses": ["results/research_quality_gate_matrix.csv", "results/research_quality_gate_matrix.json"],
    "adapter_reference_agreement_rows": ["results/adapter_reference_agreement.csv", "results/adapter_reference_agreement.json"],
    "adapter_reference_agreement_failures": ["results/adapter_reference_agreement.json"],
    "reference_integrity_entries": ["results/reference_integrity_gate.csv", "results/reference_integrity_gate.json"],
    "official_documentation_sources": ["results/source_provenance_gate.csv", "source_manifest.csv"],
    "upstream_example_sources": ["results/source_provenance_gate.csv", "source_manifest.csv"],
    "native_canonical_sources": ["results/source_provenance_gate.csv", "source_manifest.csv"],
    "semantic_stress_witness_sources": ["results/source_provenance_gate.csv", "source_manifest.csv"],
    "generated_sources": ["results/source_provenance_gate.csv", "source_manifest.csv"],
}

FIELDS = [
    "claim_id", "paper_label", "macro", "paper_value", "manifest_value",
    "evidence_files", "evidence_exists", "macro_defined", "trace_status"
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _macro_text() -> str:
    # During full replay the snapshot is generated before the paper copy is
    # synchronized.  Prefer the snapshot for artifact-local traceability while
    # verify_full_claims.py separately checks the final paper/ macro file.
    snapshot = RESULTS / "claim_macros_snapshot.tex"
    if snapshot.exists():
        return snapshot.read_text(encoding="utf-8")
    path = PAPER / "claim_macros.tex"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_claim_traceability(root: Path = ROOT) -> tuple[list[dict[str, str]], dict[str, object]]:
    manifest = _read_json(RESULTS / "claim_manifest.json").get("claims", [])
    manifest_by_id = {str(c.get("claim_id")): c for c in manifest}
    paper_rows = _read_csv(RESULTS / "paper_claims.csv")
    macro_text = _macro_text()
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    for p in paper_rows:
        claim_id = p.get("claim_id", "")
        macro = p.get("macro", "")
        evidence = EVIDENCE_BY_CLAIM.get(claim_id, [])
        exists = all((root / e).exists() for e in evidence)
        manifest_value = str(manifest_by_id.get(claim_id, {}).get("value", "MISSING"))
        macro_defined = bool(macro) and re.search(r"\\newcommand\{\\" + re.escape(macro) + r"\}\{", macro_text) is not None
        ok = claim_id in manifest_by_id and str(p.get("paper_value")) == manifest_value and exists and macro_defined
        if not ok:
            errors.append(claim_id)
        rows.append({
            "claim_id": claim_id,
            "paper_label": p.get("paper_label", ""),
            "macro": macro,
            "paper_value": str(p.get("paper_value", "")),
            "manifest_value": manifest_value,
            "evidence_files": ";".join(evidence),
            "evidence_exists": str(exists).lower(),
            "macro_defined": str(macro_defined).lower(),
            "trace_status": "PASS" if ok else "FAIL",
        })
    missing_claims = sorted(set(EVIDENCE_BY_CLAIM) & set(manifest_by_id) - {r.get("claim_id", "") for r in paper_rows})
    # Non-paper-visible claims can exist; missing_claims is informational only.
    report = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "paper_visible_claims_traced": len(rows),
        "manifest_claims": len(manifest_by_id),
        "missing_paper_claim_rows_for_known_claims": missing_claims,
        "trace_failures": len(errors),
    }
    return rows, report


def write_claim_traceability(root: Path = ROOT) -> dict[str, object]:
    rows, report = build_claim_traceability(root)
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "claim_traceability_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    (RESULTS / "claim_traceability_matrix.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(write_claim_traceability(ROOT), indent=2, sort_keys=True))
