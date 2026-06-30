import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
summary = json.loads((ROOT / 'results' / 'summary.json').read_text())
ces = json.loads((ROOT / 'results' / 'counterexamples.json').read_text())
assert summary['minimized_counterexamples'] == len(ces)
assert summary['minimized_counterexamples'] >= 240
for ce in ces[:10]:
    assert 'failure_id' in ce
    assert 'relation_id' in ce
    assert ce['replay_verified'] is True
    assert ce['observed_before_decision'] != ''
    assert ce['observed_after_decision'] != ''
print('seeded_counterexamples PASS')
