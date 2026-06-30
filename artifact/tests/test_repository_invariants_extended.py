import csv
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def read_csv(name):
    with (ROOT / 'results' / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def read_json(name):
    return json.loads((ROOT / 'results' / name).read_text())

summary = read_json('summary.json')
obligations = read_csv('obligations.csv')
rejections = read_csv('rejections.csv')
predicates = read_csv('predicate_evaluations.csv')
coverage = read_csv('coverage_lattice.csv')
manifest = read_csv('../source_manifest.csv') if (ROOT / 'source_manifest.csv').exists() else []

# Summary / obligation coherence.
applicable_rows = [r for r in obligations if r['applicability_status'] == 'APPLICABLE_EVALUATED']
assert len(applicable_rows) == summary['primary_evaluated_obligations']
assert all(r['oracle_status'] == 'PASS' for r in applicable_rows)
assert all(r['applicability_status'] == 'APPLICABLE_EVALUATED' for r in applicable_rows)
assert len(rejections) == summary['rejected_invalid_transformations']
assert len(rejections) == summary['rejected_invalid_transformations']
assert sum(1 for r in obligations if r['applicability_status'] == 'UNSUPPORTED_NOT_COUNTED') == summary['unsupported_transformations']

# Predicate ledger coherence.
assert len(predicates) == summary['predicate_witnesses']
assert all(r['computed_status'] in {'APPLICABLE_EVALUATED','REJECTED_NOT_COUNTED','UNSUPPORTED_NOT_COUNTED'} for r in predicates)
assert not any(r['computed_status'] != 'APPLICABLE_EVALUATED' and r.get('predicate_expected_invariant','not counted') != 'not counted' for r in predicates)
assert all(r['witness_hash'] for r in predicates)

# Coverage lattice coherence.
assert len(coverage) >= summary['source_ids_covered'] * summary['relation_ids_covered'] * summary['executed_real_adapters']
for row in coverage[:50]:
    assert row['adapter_id'] in {'casbin_py','cedar_py'}
    assert row['relation_id'] in {'DD','DO','PA','DA','IE','ID','HC','HR','SR','RO','AR','SM'}

# Source manifest must contain both real adapter and native fixture provenance.
source_kinds = {r.get('kind') for r in manifest}
assert 'adapter_package' in source_kinds
assert 'native_public_fixture' in source_kinds
assert any(r.get('source_id','').startswith('public_upstream_') for r in manifest)
assert all(r.get('sha256') for r in manifest if r.get('kind') in {'adapter_package','native_public_fixture','subject_corpus'})

# Public/generated scope accounting.
subject_rows = read_csv('public_subjects_manifest.csv')
public_sources = [r for r in subject_rows if r['source_id'].startswith('public_')]
generated_sources = [r for r in subject_rows if r['source_id'].startswith('generated_')]
assert len(public_sources) == summary['source_ids_covered'] - 1
assert len(generated_sources) == 0
assert any('public_upstream_cedar' in r['source_id'] for r in public_sources)
assert any('public_upstream_casbin' in r['source_id'] for r in public_sources)

# Counterexample matrix and minimization coherence.
ces = read_json('counterexamples.json')
min_rows = read_csv('minimization.csv')
assert len(ces) == summary['minimized_counterexamples']
assert len(min_rows) == summary['minimized_counterexamples']
assert all(row['validity_preserved'] == 'true' for row in min_rows)

# No paper-visible hidden failure.
claim_verification = read_json('claim_verification.json')
assert claim_verification['status'] == 'PASS'
assert claim_verification['primary_failures'] == 0
assert claim_verification['unsupported_not_counted'] == summary['unsupported_transformations']

# Model-check evidence must cover exactly the relation catalog.
model = read_json('model_check_summary.json')
assert model['status'] == 'PASS'
assert model['failures'] == 0
assert model['relations_covered'] == 12
assert model['cases_checked'] >= 74024

# Hygiene scorecard must not hide blockers.
score = read_json('repository_scorecard.json')
assert score['status'] == 'PASS'
assert score['score'] >= 100
assert not score.get('blockers')

# GitHub sync manifest must classify all paths without forcing large generated evidence into direct upload.
gh = read_csv('github_sync_manifest.csv')
assert len(gh) > 250
assert any(r['upload_mode'] == 'manifest_only' and r['path'].endswith('model_check_cases.csv') for r in gh)
assert not any('__pycache__' in r['path'] and r['upload_mode'] != 'exclude' for r in gh)
assert not any('subjects/fixtures/' in r['path'] for r in gh)

print('repository_invariants_extended PASS')
