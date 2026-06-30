from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.source_provenance_gate import build_source_provenance
rows, report = build_source_provenance(ROOT)
assert report['status'] == 'PASS', report
assert report['audited_subject_sources'] == 120, report
assert report['official_documentation_sources'] >= 5, report
assert report['upstream_example_sources'] >= 5, report
assert report['native_canonical_sources'] >= 8, report
assert report['semantic_stress_witness_sources'] == 96, report
assert report['generated_sources'] == 1, report
assert any(r['stratum']=='semantic_stress_witness' and 'not as independent upstream/public benchmark' in r['claim_safety_rule'] for r in rows)
print('source_provenance_gate PASS')
