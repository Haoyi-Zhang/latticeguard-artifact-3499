#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from latticeguard.deployed_tool_head_to_head import write_deployed_tool_head_to_head


def main() -> None:
    report = write_deployed_tool_head_to_head(ROOT)
    rows = list(csv.DictReader((ROOT / 'results' / 'deployed_tool_head_to_head.csv').open(newline='', encoding='utf-8')))
    by_id = {row['comparison_id']: row for row in rows}
    required = {
        'casbin_py-primary-point-head-to-head',
        'cedar_py-primary-point-head-to-head',
        'opa_rego_cli-primary-point-head-to-head',
        'casbin_py-seeded-point-head-to-head',
        'cedar_py-seeded-point-head-to-head',
        'cross-adapter-differential-primary-head-to-head',
    }
    errors: list[str] = []
    if report.get('status') != 'PASS':
        errors.append('deployed tool head-to-head status is not PASS')
    missing = sorted(required - set(by_id))
    if missing:
        errors.append('missing head-to-head rows: ' + ', '.join(missing))
    if int(report.get('native_adapter_count', 0)) != 2:
        errors.append('native adapter count must stay at 2')
    if int(report.get('decision_harness_count', 0)) != 1:
        errors.append('decision harness count must stay at 1')
    if report.get('opa_role') != 'normalized_decision_harness_with_supplied_closure':
        errors.append('OPA role must be normalized decision harness with supplied closure')
    if int(report.get('primary_head_to_head_stream_rows', 0)) != 15840:
        errors.append('primary head-to-head stream row count mismatch')
    if int(report.get('primary_head_to_head_failures', -1)) != 0:
        errors.append('primary head-to-head failures must be zero in the clean run')
    if int(report.get('seeded_head_to_head_stream_rows', 0)) != 36960:
        errors.append('seeded head-to-head stream row count mismatch')
    if int(report.get('seeded_law_kill_rows', 0)) != 5040:
        errors.append('seeded law-kill row count mismatch')
    if int(report.get('seeded_overlap_rows', 0)) != int(report.get('seeded_law_kill_rows', -1)):
        errors.append('seeded law kills must be covered by point-check overlap')
    if int(report.get('seeded_law_only_rows', -1)) != 0:
        errors.append('unexpected law-only seeded rows under current point-reference join')
    if int(report.get('seeded_point_only_rows', 0)) <= 0:
        errors.append('point-only seeded rows should remain visible for denominator interpretation')
    if int(report.get('missing_reference_rows', 1)) != 0:
        errors.append('missing reference rows in seeded join')
    opa_row = by_id.get('opa_rego_cli-primary-point-head-to-head', {})
    if opa_row.get('adapter_role') != 'normalized_decision_harness_with_supplied_closure':
        errors.append('OPA row role is ambiguous')
    if any(row.get('same_input_stream') != 'yes' for row in rows):
        errors.append('all head-to-head rows must declare same_input_stream=yes')
    out = {
        'status': 'PASS' if not errors else 'FAIL',
        'errors': errors,
        **report,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
