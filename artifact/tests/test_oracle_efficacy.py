from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.oracle_efficacy import baseline_effectiveness_rows

rows, report = baseline_effectiveness_rows(ROOT)
assert report['status'] == 'PASS'
assert report['full_oracle_seeded_killed'] == report['semantic_counterexamples_replayed']
assert any(r['baseline_id'] == 'LATTICEGUARD_FULL_ORACLE' and r['denominator_safety_score'] == '1.000000' for r in rows)
assert any(r['baseline_id'] == 'NO_APPLICABILITY_GATE' and int(r['invalid_transformations_admitted']) > 0 for r in rows)
print('oracle_efficacy PASS')
