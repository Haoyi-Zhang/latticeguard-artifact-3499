from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

DIMENSIONS = [
    ("paper_argument", "The main paper must stand alone: problem, law-level object, evaluation, and implications are paper-visible rather than artifact-only."),
    ("novelty_boundary", "The contribution must be distinguishable from random mutation, differential testing, upstream tests, and policy-checking surveys."),
    ("theory_depth", "The law catalog must be backed by theorem obligations, bounded model checking, and an independent executable law kernel."),
    ("evaluation_depth", "The experiment must include real adapters, public/native subjects, generated stress slices, invalid-transformation rejection, seeded drift controls, and semantic replay."),
    ("baseline_strength", "Baselines must be adversarial enough to explain why each LatticeGuard component is necessary."),
    ("claim_integrity", "Every paper-visible number must be generated from ledgers and verified after clean replay."),
    ("reproducibility", "A artifact evaluator must be able to rerun the artifact offline with deterministic outputs and hash replay."),
    ("package_hygiene", "The release packet must exclude cache/transient/generated fixture bloat while retaining scripts and deterministic ledgers."),
    ("implementation_depth", "The repository must contain first-class modules, verifiers, tests, contracts, and protocols rather than one monolithic script."),
    ("impact", "The work must explain how law-level regression oracles change evaluator maintenance practice."),
    ("open_science_policy", "The submission must include a Data Availability statement, anonymous supplement, and long-term preservation plan consistent with current ICSE open-science policy."),
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _score_dimension(root: Path, dimension: str) -> tuple[int, list[str], list[str]]:
    res = root / "results"
    summary = _read_json(res / "summary.json")
    proof = _read_json(res / "proof_certificate.json")
    mech = _read_json(res / "mechanized_law_kernel.json")
    efficacy = _read_json(res / "oracle_efficacy_summary.json")
    semantic = _read_json(res / "semantic_counterexample_replay.json")
    quality = _read_json(res / "research_quality_gate_matrix.json")
    claim = _read_json(res / "claim_verification.json")
    adapter_agreement = _read_json(res / "adapter_reference_agreement.json")
    reference_gate = _read_json(res / "reference_integrity_gate.json")
    robustness = _read_json(res / "robustness.json")
    code_files = list((root / "latticeguard").glob("*.py")) + list((root / "scripts").glob("*.py")) + list((root / "tests").glob("*.py"))
    generated_fixture_files = list((root / "subjects" / "fixtures").rglob("*")) if (root / "subjects" / "fixtures").exists() else []
    fixture_count = sum(1 for p in generated_fixture_files if p.is_file())
    issues: list[str] = []
    evidence: list[str] = []

    def need(cond: bool, issue: str, ev: str) -> None:
        if cond:
            evidence.append(ev)
        else:
            issues.append(issue)

    if dimension == "paper_argument":
        main = (root.parent / "paper" / "main.tex").read_text(encoding="utf-8", errors="ignore")
        need("law-level" in main and "applicability" in main and "LatticeGuard" in main, "main paper does not foreground the law-level oracle argument", "main.tex foregrounds law-level obligations and applicability")
        need("RQ1" in main and "RQ5" in main, "research questions are not visible in the paper", "RQ1--RQ5 are paper-visible")
    elif dimension == "novelty_boundary":
        novelty = _read_csv(res / "novelty_matrix.csv")
        need(len(novelty) >= 5, "novelty matrix below five contribution rows", f"{len(novelty)} novelty rows")
        need("differential" in (root.parent / "paper" / "main.tex").read_text(encoding="utf-8", errors="ignore").lower(), "paper does not distinguish differential testing", "paper distinguishes differential-only baselines")
    elif dimension == "theory_depth":
        theorem = _read_csv(res / "theorem_ledger.csv")
        obligations = _read_csv(res / "theorem_obligations.csv")
        need(len(theorem) == 12 and all(r.get("status") == "PASS" for r in theorem), "not all 12 relation theorems pass", "12 passing theorem rows")
        need(len(obligations) == 48 and all(r.get("status") == "PASS" for r in obligations), "proof obligations are incomplete", "48 passing proof obligations")
        need(proof.get("status") == "PASS", "proof certificate does not pass", "proof certificate PASS")
        need(mech.get("status") == "PASS" and int(mech.get("failures", 1)) == 0, "mechanized law kernel is missing or failing", f"{mech.get('cases_checked', 0)} mechanized kernel cases")
    elif dimension == "evaluation_depth":
        need(int(summary.get("primary_evaluated_obligations", 0)) >= 10000, "primary obligation count below deep-evaluation threshold", f"{summary.get('primary_evaluated_obligations', 0)} applicable obligations")
        need(int(summary.get("source_ids_covered", 0)) >= 100, "source coverage below expanded benchmark threshold", f"{summary.get('source_ids_covered', 0)} sources")
        need(int(summary.get("native_selftest_rows", 0)) >= 400, "native self-test coverage is too shallow", f"{summary.get('native_selftest_rows', 0)} native self-tests")
        need(semantic.get("status") == "PASS", "semantic counterexample replay not passing", f"{semantic.get('counterexamples_semantically_replayed', 0)} counterexamples semantically replayed")
        need(adapter_agreement.get("status") == "PASS" and int(adapter_agreement.get("failures", 1)) == 0, "adapter/reference agreement gate not passing", f"{adapter_agreement.get('rows_checked', 0)} adapter-reference agreement rows")
    elif dimension == "baseline_strength":
        need(int(efficacy.get("baseline_families", 0)) >= 9, "baseline family count below adversarial-baseline threshold", f"{efficacy.get('baseline_families', 0)} baseline families")
        baseline_rows = _read_csv(res / "baseline_results.csv")
        need(len(baseline_rows) >= 30000, "baseline row evidence is too small", f"{len(baseline_rows)} baseline rows")
    elif dimension == "claim_integrity":
        need(claim.get("status") == "PASS", "claim verifier is not passing", "claim verifier PASS")
        paper_claims = _read_csv(res / "paper_claims.csv")
        need(len(paper_claims) >= 20, "paper claim crosswalk too small", f"{len(paper_claims)} paper claim crosswalk rows")
        need(reference_gate.get("status") == "PASS", "reference-integrity gate is not passing", f"{reference_gate.get('reference_entries', 0)} cited references checked")
    elif dimension == "reproducibility":
        need(str(robustness.get("status", "")).lower() in {"pass", "passed"}, "robustness hash replay is not PASS", "robustness hash replay PASS")
        sha_rows = _read_csv(root / "evidence" / "SHA256SUMS.csv")
        need(len(sha_rows) >= 150, "SHA-256 evidence ledger too small", f"{len(sha_rows)} SHA-256 rows")
    elif dimension == "package_hygiene":
        sync = _read_csv(res / "github_sync_manifest.csv")
        need(not any("subjects/fixtures" in r.get("path", "") for r in sync), "generated fixtures appear in GitHub sync manifest", "generated fixtures excluded from sync manifest")
        need(fixture_count <= 25000, "generated fixture tree unexpectedly large", f"generated fixture files observed during replay: {fixture_count}")
    elif dimension == "implementation_depth":
        package_modules = len(list((root / "latticeguard").glob("*.py")))
        scripts = len(list((root / "scripts").glob("*.py")))
        tests = len(list((root / "tests").glob("*.py")))
        need(package_modules >= 30 and scripts >= 30 and tests >= 18, "implementation lacks module/script/test depth", f"{package_modules} modules, {scripts} scripts, {tests} tests")
        need(sum(len(p.read_text(encoding="utf-8", errors="ignore").splitlines()) for p in code_files) >= 8000, "authored Python line count below implementation-depth threshold", "authored Python line count exceeds depth threshold")
    elif dimension == "impact":
        main = (root.parent / "paper" / "main.tex").read_text(encoding="utf-8", errors="ignore")
        need("Maintainer workflow" in main, "maintainer workflow is not paper-visible", "maintainer workflow section present")
        need(quality.get("status") == "PASS", "research quality gate is not PASS", "research quality gate PASS")
    elif dimension == "open_science_policy":
        osc = _read_json(res / "open_science_compliance_gate.json")
        main = (root.parent / "paper" / "main.tex").read_text(encoding="utf-8", errors="ignore")
        supp = (root.parent / "paper" / "supplement.tex").read_text(encoding="utf-8", errors="ignore")
        has_availability = (
            "\\section{Data Availability}" in main
            or "\\section*{Data Availability}" in main
            or "\\noindent\\emph{Availability.}" in main
        )
        need(has_availability, "main paper lacks Availability statement", "main paper has Availability statement")
        need("\\section*{Acknowledg" not in supp and "\\section{Acknowledg" not in supp, "supplement contains acknowledgement section", "supplement has no acknowledgement section")
        need(osc.get("status") == "PASS", "open-science compliance gate is not PASS", "open-science compliance gate PASS")
    else:
        issues.append("unknown dimension")
    score = 100 - 7 * len(issues)
    return max(score, 0), issues, evidence


def build_venue_requirements(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    open_issues: list[str] = []
    for dimension, rationale in DIMENSIONS:
        score, issues, evidence = _score_dimension(root, dimension)
        open_issues.extend([f"{dimension}: {issue}" for issue in issues])
        rows.append({
            "dimension": dimension,
            "rationale": rationale,
            "score": score,
            "status": "PASS" if not issues else "REVIEW",
            "evidence": "; ".join(evidence),
            "remaining_issue": "; ".join(issues),
        })
    average = round(sum(int(r["score"]) for r in rows) / max(1, len(rows)), 2)
    report = {
        "status": "PASS" if not open_issues and average >= 95 else "REVIEW",
        "dimensions": len(rows),
        "average_score": average,
        "open_issues": open_issues,
    }
    return rows, report


def write_venue_requirements(root: Path) -> dict[str, Any]:
    rows, report = build_venue_requirements(root)
    out_csv = root / "results" / "venue_requirements_check.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dimension", "rationale", "score", "status", "evidence", "remaining_issue"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (root / "results" / "venue_requirements_check.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
