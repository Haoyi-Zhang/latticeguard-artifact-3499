from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from latticeguard.deployed_tool_head_to_head import _point_join_rows, deployed_tool_head_to_head_rows


rows, report = deployed_tool_head_to_head_rows(ROOT)
by_id = {row['comparison_id']: row for row in rows}

assert report['status'] == 'PASS'
assert report['native_adapter_count'] == 2
assert report['decision_harness_count'] == 1
assert report['opa_role'] == 'normalized_decision_harness_with_supplied_closure'
assert report['primary_head_to_head_stream_rows'] == 15840
assert report['primary_head_to_head_failures'] == 0
assert report['seeded_head_to_head_stream_rows'] == 36960
assert report['seeded_law_kill_rows'] == 5040
assert report['seeded_overlap_rows'] == 5040
assert report['seeded_point_only_rows'] > 0
assert report['seeded_law_only_rows'] == 0
assert by_id['opa_rego_cli-primary-point-head-to-head']['adapter_role'] == 'normalized_decision_harness_with_supplied_closure'
assert all(row['same_input_stream'] == 'yes' for row in rows)

typed_counts = _point_join_rows(
    [
        {
            'adapter_id': 'casbin_py_seeded_hierarchy',
            'candidate_id': 42,
            'before_decision': ' permitted ',
            'after_decision': 'DENIED',
            'killed': 'false',
        }
    ],
    [
        {
            'adapter_id': 'casbin_py',
            'candidate_id': '42',
            'before_decision': 'allow',
            'after_decision': 'deny',
            'applicability_status': 'APPLICABLE_EVALUATED',
        }
    ],
    'casbin_py',
)
assert typed_counts['rows'] == 1
assert typed_counts['missing_reference_rows'] == 0
assert typed_counts['deployed_failures'] == 0

print('deployed_tool_head_to_head PASS')
