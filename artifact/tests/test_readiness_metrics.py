import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.readiness_metrics import compute_readiness, report_dict, dimensions

assert (ROOT / 'results' / 'audit_objection_matrix.csv').exists()

dims = dimensions(ROOT)
assert len(dims) == 8
names = {d.name for d in dims}
assert 'replay' in names
assert 'benchmark_provenance' in names
assert 'formal_core' in names
report = compute_readiness(ROOT)
assert report.weighted_score >= 95, report
assert not report.blockers, report.blockers
payload = report_dict(report)
assert payload['recommendation'] == 'repository-ready-under-current-evidence-scope'
for dim in payload['dimensions']:
    assert dim['score'] >= 75
    assert dim['evidence']
print('readiness_metrics PASS')
