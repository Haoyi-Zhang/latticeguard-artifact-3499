from __future__ import annotations
VALIDATORS=[
    ('verify_full_claims.py','paper-visible claim ledger'),
    ('verify_predicate_witnesses.py','executable applicability witness audit'),
    ('verify_benchmark_imports.py','native fixture import and selftests'),
    ('verify_schema_contracts.py','CSV/JSON schema and denominator contract'),
    ('verify_minimization_replay.py','counterexample replay material'),
    ('verify_adapter_contracts.py','adapter semantic contract'),
    ('verify_relation_catalog.py','law catalog completeness'),
    ('evidence_query_summary.py','evidence query layer'),
    ('verify_benchmark_funnel.py','corpus inclusion/provenance funnel'),
    ('verify_counterexample_families.py','counterexample family coverage'),
    ('verify_reproducibility_contract.py','offline reproduction requirements'),
    ('verify_coverage_lattice.py','adapter x source x relation coverage'),
    ('verify_manifest_integrity.py','SHA/source manifest integrity'),
    ('verify_source_linkage.py','manifest-obligation-coverage linkage'),
    ('verify_opa_pinning.py','optional OPA pinning contract'),
    ('run_audit_lenses.py','multi-lens repository audit'),
    ('verify_result_invariants.py','result invariant checks'),
    ('repository_scorecard.py','repository readiness score'),
    ('run_unit_tests.py','library unit tests'),
    ('preflight_external_tools.py','external tool preflight'),
    ('run_drift_mining.py','real-drift witness harness'),
    ('repo_quality_audit.py','hygiene and code-size audit'),
    ('verify_anonymity_and_hygiene.py','anonymous clean packet audit'),
]

def validator_names() -> list[str]: return [v[0] for v in VALIDATORS]
def validator_purposes() -> dict[str,str]: return dict(VALIDATORS)
def registry_errors() -> list[str]: return [] if len(VALIDATORS)>=20 else ['validator registry too small']
