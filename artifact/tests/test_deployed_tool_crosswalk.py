from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from latticeguard.deployed_tool_crosswalk import deployed_tool_crosswalk_rows


rows, report = deployed_tool_crosswalk_rows(ROOT)
by_id = {row['comparison_id']: row for row in rows}

assert report['status'] == 'PASS'
assert report['release_pair_bug_claimed'] is False
assert report['only_full_oracle_has_all_features'] is True
assert by_id['latticeguard-full-oracle']['denominator_rejection'] == 'yes'
assert by_id['latticeguard-full-oracle']['minimized_failure_replay'] == 'yes'
assert int(by_id['property-generation-without-rejection']['observed_count']) > 0
assert by_id['release-pair-precheck']['release_pair_role'].startswith('future release-gating')

print('deployed_tool_crosswalk PASS')
