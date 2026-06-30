from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.research_quality_gate import quality_gate_rows
rows = quality_gate_rows(ROOT)
assert len(rows) >= 10
assert all(r['status'] == 'closed' for r in rows)
assert {r['quality_lens'] for r in rows} >= {'R1_novelty','R2_theory','R3_experiments','R4_reproducibility','R5_implementation_depth','R6_adapter_bridge','R7_reference_integrity','R8_source_provenance','R9_claim_traceability','R10_impact'}
print('research_quality_gate PASS')
