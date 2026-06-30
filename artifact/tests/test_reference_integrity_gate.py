from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.reference_integrity_gate import build_reference_rows, summarize_reference_gate

rows = build_reference_rows(ROOT.parent)
summary = summarize_reference_gate(rows, ROOT)
assert summary['status'] == 'PASS', summary
assert 70 <= summary['reference_entries'] <= 80, summary
assert summary['reference_entries'] == summary['cited_entries'], summary
print('reference_integrity_gate PASS')
