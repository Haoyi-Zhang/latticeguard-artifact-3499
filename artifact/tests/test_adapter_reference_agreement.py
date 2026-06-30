from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.adapter_reference_agreement import build_agreement_rows, summarize_agreement

rows = build_agreement_rows(ROOT)
summary = summarize_agreement(rows)
assert summary['status'] == 'PASS', summary
assert summary['rows_checked'] >= 10000, summary
assert summary['adapters_covered'] >= 2, summary
assert summary['relations_covered'] == 12, summary
print('adapter_reference_agreement PASS')
