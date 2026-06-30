import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.benchmark_importers import native_subject_records, benchmark_manifest_rows
records = native_subject_records()
assert len(records) >= 17, len(records)
assert sum(1 for r in records if r.source_id.startswith('public_upstream_')) >= 7
assert {r.family for r in records} >= {'casbin', 'cedar'}
for rec in records:
    assert rec.fixture_ids
    assert rec.license == 'Apache-2.0'
print('benchmark_importers PASS')
