from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.claim_traceability import build_claim_traceability
rows, report = build_claim_traceability(ROOT)
assert report['status'] == 'PASS', report
assert report['paper_visible_claims_traced'] >= 30, report
ids = {r['claim_id'] for r in rows}
for required in ['primary_evaluated_obligations','adapter_reference_agreement_rows','source_ids_covered','semantic_stress_witness_sources']:
    assert required in ids, required
assert all(r['trace_status'] == 'PASS' for r in rows)
print('claim_traceability PASS')
