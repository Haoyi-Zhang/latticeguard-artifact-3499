from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.mechanized_law_kernel import RELATIONS, generate_kernel_rows, build_summary

rows = generate_kernel_rows()
summary = build_summary(rows)
assert summary['status'] == 'PASS'
assert summary['relations_covered'] == len(RELATIONS)
assert summary['failures'] == 0
assert len(rows) >= 400
for rid in RELATIONS:
    assert sum(1 for r in rows if r['relation_id'] == rid) >= 30, rid
print('mechanized_law_kernel PASS')
