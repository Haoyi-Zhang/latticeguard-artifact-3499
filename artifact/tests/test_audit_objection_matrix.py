import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
with (ROOT / 'results' / 'audit_objection_matrix.csv').open(newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
assert len(rows) >= 7
lenses = {r['lens'] for r in rows}
required = {
    'artifact_reproducibility',
    'formal_soundness',
    'applicability_discipline',
    'benchmark_provenance',
    'counterexample_replay',
    'repository_hygiene',
    'scale',
}
assert required <= lenses
for row in rows:
    assert row['objection']
    assert row['evidence_file']
    assert row['repair_status']
    assert row['residual_risk']
    evidence = ROOT / row['evidence_file']
    assert evidence.exists(), evidence
    if row['lens'] == 'scale':
        assert 'primary obligations' in row['repair_status']
    if row['lens'] == 'formal_soundness':
        assert 'bounded' in row['repair_status'].lower()
    if row['lens'] == 'benchmark_provenance':
        assert row['evidence_file'].endswith('native_selftest_results.csv')
print('audit_objection_matrix PASS')
# The matrix is intentionally executable: every assessor lens must have a concrete file.
for evidence in sorted({row['evidence_file'] for row in rows}):
    assert (ROOT / evidence).is_file()
