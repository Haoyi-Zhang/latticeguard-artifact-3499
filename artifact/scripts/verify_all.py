#!/usr/bin/env python3
from __future__ import annotations
import csv, json, os, shutil, sys, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from latticeguard.runtime_hygiene import cleanup_bytecode_artifacts, python_bytecode_env, scan_bytecode_artifacts
REQUIRED_RESULTS=['summary.json', 'claim_manifest.json', 'predicate_evaluations.csv', 'soundness_checks.csv', 'model_check_summary.json', 'native_selftest_results.csv', 'obligations.csv', 'rejections.csv', 'counterexamples.json', 'coverage_lattice.csv', 'repository_scorecard.json', 'upstream_benchmark_audit.csv', 'github_sync_manifest.csv', 'audit_objection_matrix.csv', 'repository_readiness_metrics.json', 'repository_depth.json', 'artifact_depth.json', 'obligation_slice_matrix.csv', 'proof_certificate.json', 'theorem_ledger.csv', 'theorem_obligations.csv', 'research_questions.csv', 'novelty_matrix.csv', 'research_quality_matrix.csv', 'quality_lens_score.json', 'experimental_design_matrix.csv', 'overfitting_audit.csv', 'overfitting_audit.json', 'validity_challenge_evidence.csv', 'validity_challenge_evidence.json', 'validity_boundary_evidence.csv', 'validity_boundary_evidence.json', 'applicability_breakdown.csv', 'rejection_examples.csv', 'seeded_drift_sensitivity.csv', 'source_boundary_summary.csv', 'evidence_challenge_findings.csv', 'evidence_challenge_repair_matrix.csv', 'paper_impact_matrix.csv', 'evidence_challenge_check.json', 'semantic_counterexample_replay.json', 'semantic_counterexample_replay.csv', 'mechanized_law_kernel.csv', 'mechanized_law_kernel.json', 'oracle_efficacy_summary.csv', 'oracle_efficacy_summary.json', 'deployed_tool_crosswalk.csv', 'deployed_tool_crosswalk.json', 'deployed_tool_head_to_head.csv', 'deployed_tool_head_to_head.json', 'research_quality_gate_matrix.csv', 'research_quality_gate_matrix.json', 'venue_requirements_check.csv', 'venue_requirements_check.json', 'artifact_manifest.csv', 'artifact_integrity_check.json', 'adapter_reference_agreement.csv', 'adapter_reference_agreement.json', 'reference_integrity_gate.csv', 'reference_integrity_gate.json', 'source_provenance_gate.csv', 'source_provenance_gate.json', 'claim_traceability_matrix.csv', 'claim_traceability_matrix.json', 'dependency_provenance_gate.csv', 'dependency_provenance_gate.json', 'module_import_gate.csv', 'module_import_gate.json', 'denominator_integrity_gate.csv', 'denominator_integrity_gate.json', 'protocol_freeze_gate.csv', 'protocol_freeze_gate.json', 'content_residue_gate.csv', 'content_residue_gate.json', 'resource_license_gate.csv', 'resource_license_gate.json', 'import_surface_gate.csv', 'import_surface_gate.json', 'narrative_claim_scan_gate.csv', 'narrative_claim_scan_gate.json', 'reproducibility_risk_check.csv', 'reproducibility_risk_check.json', 'manuscript_presentation_gate.csv', 'manuscript_presentation_gate.json', 'open_science_compliance_gate.csv', 'open_science_compliance_gate.json']
AUTO_GENERATE={'upstream_benchmark_audit.csv': 'verify_upstream_benchmarks.py', 'github_sync_manifest.csv': 'export_github_sync_manifest.py', 'audit_objection_matrix.csv': 'verify_objection_matrix.py', 'repository_readiness_metrics.json': 'verify_readiness_metrics.py', 'repository_depth.json': 'verify_repository_depth.py', 'artifact_depth.json': 'verify_artifact_depth.py', 'obligation_slice_matrix.csv': 'verify_obligation_slicing.py', 'theorem_ledger.csv': 'verify_theorem_ledger.py', 'theorem_obligations.csv': 'verify_theorem_ledger.py', 'proof_certificate.json': 'verify_proof_certificate.py', 'research_questions.csv': 'verify_research_quality.py', 'novelty_matrix.csv': 'verify_research_quality.py', 'research_quality_matrix.csv': 'verify_research_quality.py', 'quality_lens_score.json': 'quality_lens_score.py', 'experimental_design_matrix.csv': 'verify_experimental_design.py', 'overfitting_audit.csv': 'verify_overfitting_audit.py', 'overfitting_audit.json': 'verify_overfitting_audit.py', 'validity_challenge_evidence.csv': 'verify_validity_challenge_evidence.py', 'validity_challenge_evidence.json': 'verify_validity_challenge_evidence.py', 'validity_boundary_evidence.csv': 'verify_validity_boundary_evidence.py', 'validity_boundary_evidence.json': 'verify_validity_boundary_evidence.py', 'applicability_breakdown.csv': 'verify_validity_boundary_evidence.py', 'rejection_examples.csv': 'verify_validity_boundary_evidence.py', 'seeded_drift_sensitivity.csv': 'verify_validity_boundary_evidence.py', 'source_boundary_summary.csv': 'verify_validity_boundary_evidence.py', 'evidence_challenge_findings.csv': 'verify_evidence_challenge_check.py', 'evidence_challenge_repair_matrix.csv': 'verify_evidence_challenge_check.py', 'paper_impact_matrix.csv': 'verify_evidence_challenge_check.py', 'evidence_challenge_check.json': 'verify_evidence_challenge_check.py', 'semantic_counterexample_replay.json': 'verify_semantic_counterexample_replay.py', 'semantic_counterexample_replay.csv': 'verify_semantic_counterexample_replay.py', 'mechanized_law_kernel.csv': 'verify_mechanized_law_kernel.py', 'mechanized_law_kernel.json': 'verify_mechanized_law_kernel.py', 'oracle_efficacy_summary.csv': 'verify_oracle_efficacy.py', 'oracle_efficacy_summary.json': 'verify_oracle_efficacy.py', 'deployed_tool_crosswalk.csv': 'verify_deployed_tool_crosswalk.py', 'deployed_tool_crosswalk.json': 'verify_deployed_tool_crosswalk.py', 'deployed_tool_head_to_head.csv': 'verify_deployed_tool_head_to_head.py', 'deployed_tool_head_to_head.json': 'verify_deployed_tool_head_to_head.py', 'research_quality_gate_matrix.csv': 'verify_research_quality_gate.py', 'research_quality_gate_matrix.json': 'verify_research_quality_gate.py', 'venue_requirements_check.csv': 'verify_venue_requirements.py', 'venue_requirements_check.json': 'verify_venue_requirements.py', 'artifact_manifest.csv': 'verify_artifact_integrity_check.py', 'artifact_integrity_check.json': 'verify_artifact_integrity_check.py', 'adapter_reference_agreement.csv': 'verify_adapter_reference_agreement.py', 'adapter_reference_agreement.json': 'verify_adapter_reference_agreement.py', 'reference_integrity_gate.csv': 'verify_reference_integrity_gate.py', 'reference_integrity_gate.json': 'verify_reference_integrity_gate.py', 'source_provenance_gate.csv': 'verify_source_provenance_gate.py', 'source_provenance_gate.json': 'verify_source_provenance_gate.py', 'claim_traceability_matrix.csv': 'verify_claim_traceability.py', 'claim_traceability_matrix.json': 'verify_claim_traceability.py', 'dependency_provenance_gate.csv': 'verify_dependency_provenance_gate.py', 'dependency_provenance_gate.json': 'verify_dependency_provenance_gate.py', 'module_import_gate.csv': 'verify_module_import_gate.py', 'module_import_gate.json': 'verify_module_import_gate.py', 'denominator_integrity_gate.csv': 'verify_denominator_integrity_gate.py', 'denominator_integrity_gate.json': 'verify_denominator_integrity_gate.py', 'protocol_freeze_gate.csv': 'verify_protocol_freeze_gate.py', 'protocol_freeze_gate.json': 'verify_protocol_freeze_gate.py', 'content_residue_gate.csv': 'verify_content_residue_gate.py', 'content_residue_gate.json': 'verify_content_residue_gate.py', 'resource_license_gate.csv': 'verify_resource_license_gate.py', 'resource_license_gate.json': 'verify_resource_license_gate.py', 'import_surface_gate.csv': 'verify_import_surface_gate.py', 'import_surface_gate.json': 'verify_import_surface_gate.py', 'narrative_claim_scan_gate.csv': 'verify_narrative_claim_scan_gate.py', 'narrative_claim_scan_gate.json': 'verify_narrative_claim_scan_gate.py', 'reproducibility_risk_check.csv': 'verify_reproducibility_risk_check.py', 'reproducibility_risk_check.json': 'verify_reproducibility_risk_check.py', 'manuscript_presentation_gate.csv': 'verify_manuscript_presentation_gate.py', 'manuscript_presentation_gate.json': 'verify_manuscript_presentation_gate.py', 'open_science_compliance_gate.csv': 'verify_open_science_compliance_gate.py', 'open_science_compliance_gate.json': 'verify_open_science_compliance_gate.py', 'claim_verification.json': 'verify_full_claims.py'}
def _clean_env():
    return python_bytecode_env()

TRANSIENT_DIR_NAMES = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
TRANSIENT_SUFFIXES = {'.pyc', '.pyo'}

def clean_release_residue() -> None:
    for path in sorted(ROOT.parent.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and path.name in TRANSIENT_DIR_NAMES:
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() and path.suffix in TRANSIENT_SUFFIXES:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

FORCE_STATUS={'venue_requirements_check.json','reproducibility_risk_check.json','artifact_integrity_check.json','dependency_provenance_gate.json','module_import_gate.json','denominator_integrity_gate.json','protocol_freeze_gate.json','content_residue_gate.json','resource_license_gate.json','import_surface_gate.json','narrative_claim_scan_gate.json','manuscript_presentation_gate.json','open_science_compliance_gate.json','research_quality_gate_matrix.json','validity_boundary_evidence.json','deployed_tool_crosswalk.json','deployed_tool_head_to_head.json'}

def _json_status(path: Path) -> str:
    if not path.exists(): return ''
    try: return str(json.loads(path.read_text(encoding='utf-8')).get('status',''))
    except Exception: return ''

def ensure_generated_results() -> None:
    # Bootstrap the primary replay ledgers when an auditor invokes verify_all
    # from a clean or partially cleaned artifact.  The documented full replay
    # still runs run_full_evaluation.py explicitly, but the aggregate gate
    # should not fail just because generated CSV ledgers are absent.
    core_ledgers = [
        'summary.json',
        'obligations.csv',
        'predicate_evaluations.csv',
        'soundness_checks.csv',
        'model_check_summary.json',
        'native_selftest_results.csv',
        'coverage_lattice.csv',
    ]
    if any(not (ROOT/'results'/name).exists() for name in core_ledgers):
        subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/'run_full_evaluation.py')], cwd=str(ROOT), env=_clean_env(), check=True, stdout=subprocess.DEVNULL)
    # Always refresh the hash replay ledger before aggregate checking.  This
    # makes verify_all a self-healing clean-package entry point rather than a
    # reader of stale robustness state after deterministic gate rewrites.
    subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/'verify_robustness_replay.py')], cwd=str(ROOT), env=_clean_env(), check=True, stdout=subprocess.DEVNULL)
    claim_target=ROOT/'results'/'claim_verification.json'
    deferred_after_claims = {'venue_requirements_check.csv', 'venue_requirements_check.json'}
    deferred_after_claims_and_objections = {'repository_readiness_metrics.json'}
    handled_explicitly = deferred_after_claims | {'claim_verification.json'}
    handled_explicitly |= deferred_after_claims_and_objections | {'audit_objection_matrix.csv'}
    for result_name, script_name in AUTO_GENERATE.items():
        if result_name in handled_explicitly:
            continue
        target=ROOT/'results'/result_name
        status=_json_status(target) if target.suffix=='.json' else ''
        if (not target.exists()) or (result_name in FORCE_STATUS and status not in {'PASS','passed'}):
            subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/script_name)], cwd=str(ROOT), env=_clean_env(), check=True, stdout=subprocess.DEVNULL)
    # Claim verification depends on the generated quality/depth/provenance
    # ledgers above.  The objection matrix in turn cites claim_verification,
    # and repository readiness scores the objection matrix, so those gates run
    # in that order rather than relying on stale retained CSVs.
    subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/'verify_full_claims.py')], cwd=str(ROOT), env=_clean_env(), check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/'verify_objection_matrix.py')], cwd=str(ROOT), env=_clean_env(), check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/'verify_readiness_metrics.py')], cwd=str(ROOT), env=_clean_env(), check=True, stdout=subprocess.DEVNULL)
    deferred_scripts = sorted({AUTO_GENERATE[result_name] for result_name in deferred_after_claims})
    for script_name in deferred_scripts:
        subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/script_name)], cwd=str(ROOT), env=_clean_env(), check=True, stdout=subprocess.DEVNULL)
    sys.path.insert(0, str(ROOT/'scripts'))
    import run_full_evaluation as rfe  # type: ignore
    clean_release_residue()
    subprocess.run([sys.executable, '-B', str(ROOT/'scripts'/'verify_artifact_integrity_check.py')], cwd=str(ROOT), env=_clean_env(), check=True, stdout=subprocess.DEVNULL)
    clean_release_residue()
    rfe.write_hashes()

def read_json(path: Path): return json.loads(path.read_text(encoding='utf-8'))
def read_csv_rows(path: Path) -> list[dict[str,str]]:
    with path.open('r', encoding='utf-8', newline='') as f: return list(csv.DictReader(f))
def count_csv(path: Path) -> int: return len(read_csv_rows(path))

def main() -> None:
    cleanup_bytecode_artifacts(ROOT)
    ensure_generated_results()
    errors=[]
    for name in REQUIRED_RESULTS:
        if not (ROOT/'results'/name).exists(): errors.append('missing results/'+name)
    if not errors:
        summary=read_json(ROOT/'results'/'summary.json'); score=read_json(ROOT/'results'/'repository_scorecard.json'); model=read_json(ROOT/'results'/'model_check_summary.json')
        if score.get('status')!='PASS': errors.append('repository_scorecard status is not PASS')
        if int(summary.get('primary_evaluated_obligations',0)) < 10000: errors.append('primary obligations below expanded threshold')
        if int(summary.get('native_selftest_failures',1)) != 0: errors.append('native selftest failures present')
        if int(model.get('failures',1)) != 0: errors.append('bounded model check failures present')
        if count_csv(ROOT/'results'/'predicate_evaluations.csv') != int(summary.get('predicate_witnesses',0)): errors.append('predicate witness ledger size mismatch')
        if count_csv(ROOT/'results'/'native_selftest_results.csv') < 400: errors.append('native selftest ledger below threshold')
        if count_csv(ROOT/'results'/'coverage_lattice.csv') < int(summary.get('source_ids_covered',0))*int(summary.get('relation_ids_covered',0))*int(summary.get('executed_real_adapters',0)): errors.append('coverage lattice below adapter-source-relation grid')
        for rel,status_key in [
            ('repository_readiness_metrics.json','weighted_score'),('repository_depth.json','status'),('artifact_depth.json','status'),('proof_certificate.json','status'),('quality_lens_score.json','status'),('evidence_challenge_check.json','status'),('validity_challenge_evidence.json','status'),('validity_boundary_evidence.json','status'),('mechanized_law_kernel.json','status'),('oracle_efficacy_summary.json','status'),('deployed_tool_crosswalk.json','status'),('deployed_tool_head_to_head.json','status'),('research_quality_gate_matrix.json','status'),('venue_requirements_check.json','status'),('artifact_integrity_check.json','status'),('adapter_reference_agreement.json','status'),('reference_integrity_gate.json','status'),('source_provenance_gate.json','status'),('claim_traceability_matrix.json','status'),('dependency_provenance_gate.json','status'),('module_import_gate.json','status'),('denominator_integrity_gate.json','status'),('protocol_freeze_gate.json','status'),('content_residue_gate.json','status'),('resource_license_gate.json','status'),('import_surface_gate.json','status'),('narrative_claim_scan_gate.json','status'),('manuscript_presentation_gate.json','status'),('reproducibility_risk_check.json','status'),('open_science_compliance_gate.json','status')]:
            obj=read_json(ROOT/'results'/rel)
            if status_key=='weighted_score':
                if float(obj.get('weighted_score',0)) < 95: errors.append(rel+' weighted_score below 95')
            elif obj.get('status') not in {'PASS','passed'}: errors.append(rel+' status is not PASS')
        if count_csv(ROOT/'results'/'theorem_ledger.csv') != 12: errors.append('theorem ledger must have 12 rows')
        if count_csv(ROOT/'results'/'theorem_obligations.csv') != 48: errors.append('theorem obligations must have 48 rows')
        if count_csv(ROOT/'results'/'research_questions.csv') != 5: errors.append('research question matrix must have 5 rows')
        if count_csv(ROOT/'results'/'novelty_matrix.csv') < 5: errors.append('novelty matrix too small')
        if count_csv(ROOT/'results'/'research_quality_matrix.csv') < 6: errors.append('research quality matrix too small')
        if int(read_json(ROOT/'results'/'semantic_counterexample_replay.json').get('counterexamples_semantically_replayed',0)) != int(summary.get('minimized_counterexamples',-1)): errors.append('semantic replay count mismatch')
        if int(read_json(ROOT/'results'/'mechanized_law_kernel.json').get('relations_covered',0)) != 12: errors.append('mechanized kernel relation coverage mismatch')
        deployed=read_json(ROOT/'results'/'deployed_tool_crosswalk.json')
        if int(deployed.get('rows',0)) < 8 or deployed.get('only_full_oracle_has_all_features') is not True: errors.append('deployed tool crosswalk does not separate deployed idioms from the full oracle')
        if deployed.get('release_pair_bug_claimed') is not False: errors.append('release-pair crosswalk must not claim a current public bug witness')
        deployed_h2h=read_json(ROOT/'results'/'deployed_tool_head_to_head.json')
        if int(deployed_h2h.get('rows',0)) < 6: errors.append('deployed tool head-to-head rows insufficient')
        if int(deployed_h2h.get('native_adapter_count',0)) != 2 or int(deployed_h2h.get('decision_harness_count',0)) != 1: errors.append('deployed head-to-head must separate two native adapters from one decision harness')
        if deployed_h2h.get('opa_role') != 'normalized_decision_harness_with_supplied_closure': errors.append('OPA role in head-to-head evidence is ambiguous')
        if int(deployed_h2h.get('primary_head_to_head_stream_rows',0)) != int(summary.get('primary_evaluated_obligations',-1)): errors.append('primary head-to-head stream rows do not match primary obligations')
        if int(deployed_h2h.get('primary_head_to_head_failures',-1)) != int(summary.get('primary_real_failures',-2)): errors.append('primary head-to-head failure count mismatch')
        if int(deployed_h2h.get('seeded_head_to_head_stream_rows',0)) != int(summary.get('seeded_mutant_rows',-1)): errors.append('seeded head-to-head stream rows do not match seeded rows')
        if int(deployed_h2h.get('seeded_law_kill_rows',0)) != int(summary.get('seeded_mutants_killed',-1)): errors.append('seeded head-to-head law kills do not match seeded kills')
        if int(deployed_h2h.get('seeded_overlap_rows',0)) != int(summary.get('seeded_mutants_killed',-1)): errors.append('seeded head-to-head overlap does not cover all law kills')
        if int(deployed_h2h.get('seeded_law_only_rows',-1)) != 0 or int(deployed_h2h.get('missing_reference_rows',1)) != 0: errors.append('seeded head-to-head join is incomplete')
        if int(read_json(ROOT/'results'/'adapter_reference_agreement.json').get('rows_checked',0)) != int(summary.get('primary_evaluated_obligations',-1)): errors.append('adapter/reference rows mismatch')
        if int(read_json(ROOT/'results'/'reference_integrity_gate.json').get('reference_entries',0)) != 73: errors.append('reference integrity entry count mismatch')
        prov=read_json(ROOT/'results'/'source_provenance_gate.json')
        if int(prov.get('classified_sources', prov.get('audited_subject_sources',0))) != int(summary.get('source_ids_covered',-1)): errors.append('source provenance count mismatch')
        if int(prov.get('semantic_stress_witness_sources',0)) != 96: errors.append('semantic stress source count mismatch')
        trace=read_json(ROOT/'results'/'claim_traceability_matrix.json')
        if int(trace.get('trace_failures',1)) != 0 or int(trace.get('paper_visible_claims_traced',0)) < 30: errors.append('claim traceability insufficient')
        rqgate=read_json(ROOT/'results'/'research_quality_gate_matrix.json')
        if int(rqgate.get('quality_lenses',0)) < 19 or int(rqgate.get('open_gaps',1)) != 0: errors.append('research quality gate coverage insufficient')
        validity=read_json(ROOT/'results'/'validity_challenge_evidence.json')
        if int(validity.get('checks',0)) < 7 or int(validity.get('failures',1)) != 0: errors.append('validity challenge evidence insufficient')
        if validity.get('opa_native_closure_claimed') is not False: errors.append('OPA native closure must not be claimed')
        if int(validity.get('holdout_relation_count',0)) != 12 or int(validity.get('holdout_adapter_count',0)) != 3: errors.append('holdout challenge coverage insufficient')
        boundary=read_json(ROOT/'results'/'validity_boundary_evidence.json')
        if int(boundary.get('checks',0)) < 14 or int(boundary.get('failures',1)) != 0: errors.append('validity boundary evidence insufficient')
        if boundary.get('opa_native_closure_claimed') is not False: errors.append('validity boundary OPA fragment claim insufficient')
        if float(boundary.get('seeded_kill_rate_percent','0')) <= 0.0 or count_csv(ROOT/'results'/'applicability_breakdown.csv') < 30: errors.append('validity boundary breakdown insufficient')
        protocol=read_json(ROOT/'results'/'protocol_freeze_gate.json')
        if int(protocol.get('checks',0)) < 10 or int(protocol.get('failures',1)) != 0: errors.append('protocol-freeze gate insufficient')
        conf=read_json(ROOT/'results'/'venue_requirements_check.json')
        if int(conf.get('dimensions',0)) < 10 or float(conf.get('average_score',0)) < 95: errors.append('venue requirements score insufficient')
        delivery=read_json(ROOT/'results'/'reproducibility_risk_check.json')
        if int(delivery.get('risk_rows',0)) < 21 or int(delivery.get('open_risks',1)) != 0: errors.append('reproducibility risk gate coverage insufficient')
        import_surface=read_json(ROOT/'results'/'import_surface_gate.json')
        if int(import_surface.get('scanned_python_files',0)) < 100 or import_surface.get('undeclared_external_imports'): errors.append('import surface closure insufficient')
        narrative=read_json(ROOT/'results'/'narrative_claim_scan_gate.json')
        if int(narrative.get('failures',1)) != 0 or int(narrative.get('narrative_claim_rows',0)) < 12: errors.append('narrative claim scan insufficient')
        manuscript=read_json(ROOT/'results'/'manuscript_presentation_gate.json')
        if int(manuscript.get('failures',1)) != 0 or int(manuscript.get('presentation_checks',0)) < 9: errors.append('manuscript presentation gate insufficient')
        openscience=read_json(ROOT/'results'/'open_science_compliance_gate.json')
        if int(openscience.get('failures',1)) != 0 or int(openscience.get('open_science_checks',0)) < 6: errors.append('open science compliance gate insufficient')

    removed = cleanup_bytecode_artifacts(ROOT)
    remaining = [path.relative_to(ROOT).as_posix() for path in scan_bytecode_artifacts(ROOT)]
    if remaining:
        errors.append('bytecode residue remains after cleanup: ' + ', '.join(remaining[:20]))
    report={'status':'PASS' if not errors else 'FAIL','checks':129,'errors':errors,'bytecode_cleanup_removed':len(removed),'bytecode_residue_remaining':len(remaining),'note':'Aggregate verifier over first-class ledgers, validity-boundary evidence, protocol-freeze checks, and specialized reproducibility checks.'}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
