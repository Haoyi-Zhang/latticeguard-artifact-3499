import csv
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.upstream_benchmarks import upstream_rows

rows = upstream_rows(ROOT / 'source_manifest.csv', ROOT / 'results' / 'native_selftest_results.csv')
assert rows, 'expected upstream/native benchmark audit rows'
assert all(r.verdict == 'PASS' for r in rows), [r for r in rows if r.verdict != 'PASS']
assert sum(1 for r in rows if r.source_id.startswith('public_upstream_')) >= 7
assert {r.family for r in rows} >= {'casbin', 'cedar'}
print('upstream_benchmarks PASS')
