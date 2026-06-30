#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from latticeguard.deployed_tool_crosswalk import write_deployed_tool_crosswalk


def main() -> None:
    report = write_deployed_tool_crosswalk(ROOT)
    rows = list(csv.DictReader((ROOT / 'results' / 'deployed_tool_crosswalk.csv').open(newline='', encoding='utf-8')))
    by_id = {row['comparison_id']: row for row in rows}
    required = {
        'casbin-native-fixture-tests',
        'cedar-native-fixture-tests',
        'opa-policy-tests',
        'xacml-rbac-request-generation',
        'cross-adapter-differential',
        'property-generation-without-rejection',
        'release-pair-precheck',
        'latticeguard-full-oracle',
    }
    errors: list[str] = []
    if report.get('status') != 'PASS':
        errors.append('deployed tool crosswalk status is not PASS')
    missing = sorted(required - set(by_id))
    if missing:
        errors.append('missing deployed idiom rows: ' + ', '.join(missing))
    full = by_id.get('latticeguard-full-oracle', {})
    for field in ['law_level_obligation_support', 'applicability_gate', 'denominator_rejection', 'minimized_failure_replay']:
        if full.get(field) != 'yes':
            errors.append('full oracle lacks ' + field)
    non_full_all_features = [
        row['comparison_id']
        for row in rows
        if row['comparison_id'] != 'latticeguard-full-oracle'
        and all(row.get(field) == 'yes' for field in ['law_level_obligation_support', 'applicability_gate', 'denominator_rejection', 'minimized_failure_replay'])
    ]
    if non_full_all_features:
        errors.append('non-full baselines claim all oracle features: ' + ', '.join(non_full_all_features))
    if int(report.get('native_selftest_rows', 0)) < 400:
        errors.append('native deployed-test evidence below threshold')
    if int(report.get('cross_adapter_comparable_rows', 0)) <= 0:
        errors.append('cross-adapter deployed comparison has no comparable rows')
    if int(report.get('invalid_transformations_rejected', 0)) <= 0:
        errors.append('denominator rejection evidence missing')
    if report.get('release_pair_bug_claimed') is not False:
        errors.append('release-pair row must not claim a current public bug witness')
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
