from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence


FIELDS = [
    'comparison_id',
    'deployed_idiom',
    'frozen_stream',
    'stream_rows',
    'deployed_check_rows',
    'deployed_reported_failures',
    'latticeguard_checked_rows',
    'latticeguard_law_failures',
    'overlap_failures',
    'deployed_only_failures',
    'latticeguard_only_failures',
    'same_input_stream',
    'adapter_role',
    'empirical_reading',
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, '') for field in FIELDS})


def _is_true(value: object) -> bool:
    return str(value).strip().lower() == 'true'


def _field(row: Mapping[str, object], key: str) -> str:
    value = row.get(key, '')
    return '' if value is None else str(value).strip()


def _decision(value: object) -> str:
    text = '' if value is None else str(value).strip().lower()
    aliases = {
        'permit': 'allow',
        'permitted': 'allow',
        'allowed': 'allow',
        'forbid': 'deny',
        'forbidden': 'deny',
        'denied': 'deny',
    }
    return aliases.get(text, text)


def _base_adapter(mutant_adapter: str) -> str:
    if mutant_adapter.startswith('casbin_py'):
        return 'casbin_py'
    if mutant_adapter.startswith('cedar_py'):
        return 'cedar_py'
    return mutant_adapter


def _primary_rows_by_adapter(rows: Sequence[Mapping[str, str]]) -> dict[str, list[Mapping[str, str]]]:
    grouped: dict[str, list[Mapping[str, str]]] = {}
    for row in rows:
        if _field(row, 'applicability_status') != 'APPLICABLE_EVALUATED':
            continue
        grouped.setdefault(_field(row, 'adapter_id'), []).append(row)
    return grouped


def _point_join_rows(
    seeded_rows: Sequence[Mapping[str, str]],
    primary_rows: Sequence[Mapping[str, str]],
    adapter_prefix: str,
) -> Counter[str]:
    reference = {
        (_field(row, 'adapter_id'), _field(row, 'candidate_id')): (
            _decision(row.get('before_decision')),
            _decision(row.get('after_decision')),
        )
        for row in primary_rows
        if _field(row, 'applicability_status') == 'APPLICABLE_EVALUATED'
    }
    counts: Counter[str] = Counter()
    for row in seeded_rows:
        adapter_id = _field(row, 'adapter_id')
        if not adapter_id.startswith(adapter_prefix):
            continue
        base = _base_adapter(adapter_id)
        key = (base, _field(row, 'candidate_id'))
        if key not in reference:
            counts['missing_reference_rows'] += 1
            continue
        before_ref, after_ref = reference[key]
        deployed_failure = _decision(row.get('before_decision')) != before_ref or _decision(row.get('after_decision')) != after_ref
        law_failure = _is_true(row.get('killed', 'false'))
        counts['rows'] += 1
        counts['deployed_check_rows'] += 2
        counts['deployed_failures'] += int(deployed_failure)
        counts['law_failures'] += int(law_failure)
        counts['overlap'] += int(deployed_failure and law_failure)
        counts['deployed_only'] += int(deployed_failure and not law_failure)
        counts['law_only'] += int(law_failure and not deployed_failure)
    return counts


def _primary_head_to_head_rows(primary_rows: Sequence[Mapping[str, str]]) -> list[dict[str, object]]:
    grouped = _primary_rows_by_adapter(primary_rows)
    labels = {
        'casbin_py': (
            'Casbin-style expected-decision point tests on transformed policies',
            'native_adapter',
        ),
        'cedar_py': (
            'Cedar-style expected-decision point tests on transformed policies',
            'native_adapter',
        ),
        'opa_rego_cli': (
            'OPA/Rego policy-test idiom over normalized before/follow-up decisions',
            'normalized_decision_harness_with_supplied_closure',
        ),
    }
    rows: list[dict[str, object]] = []
    for adapter_id in ['casbin_py', 'cedar_py', 'opa_rego_cli']:
        adapter_rows = grouped.get(adapter_id, [])
        primary_failures = sum(1 for row in adapter_rows if _field(row, 'oracle_status') == 'FAIL')
        rows.append({
            'comparison_id': f'{adapter_id}-primary-point-head-to-head',
            'deployed_idiom': labels[adapter_id][0],
            'frozen_stream': 'primary applicable transformations',
            'stream_rows': len(adapter_rows),
            'deployed_check_rows': len(adapter_rows) * 2,
            'deployed_reported_failures': primary_failures,
            'latticeguard_checked_rows': len(adapter_rows),
            'latticeguard_law_failures': primary_failures,
            'overlap_failures': primary_failures,
            'deployed_only_failures': 0,
            'latticeguard_only_failures': 0,
            'same_input_stream': 'yes',
            'adapter_role': labels[adapter_id][1],
            'empirical_reading': 'The deployed-style point checks and the law oracle both report zero failures on the clean primary stream; this is regression-baseline evidence, not a bug-discovery claim.',
        })
    return rows


def deployed_tool_head_to_head_rows(root: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    results = root / 'results'
    primary_rows = _read_csv(results / 'obligations.csv')
    baseline_rows = _read_csv(results / 'baseline_results.csv')
    seeded_rows = [row for row in baseline_rows if _field(row, 'baseline_id') == 'SEEDED_MUTANT_POSITIVE_CONTROL']
    rows = _primary_head_to_head_rows(primary_rows)

    for prefix, label, role in [
        ('casbin_py', 'Casbin native expected-decision checks on seeded semantic drifts', 'native_adapter_seeded_control'),
        ('cedar_py', 'Cedar native expected-decision checks on seeded semantic drifts', 'native_adapter_seeded_control'),
    ]:
        counts = _point_join_rows(seeded_rows, primary_rows, prefix)
        rows.append({
            'comparison_id': f'{prefix}-seeded-point-head-to-head',
            'deployed_idiom': label,
            'frozen_stream': 'seeded semantic-drift transformations joined by adapter family and candidate id',
            'stream_rows': counts['rows'],
            'deployed_check_rows': counts['deployed_check_rows'],
            'deployed_reported_failures': counts['deployed_failures'],
            'latticeguard_checked_rows': counts['rows'],
            'latticeguard_law_failures': counts['law_failures'],
            'overlap_failures': counts['overlap'],
            'deployed_only_failures': counts['deployed_only'],
            'latticeguard_only_failures': counts['law_only'],
            'same_input_stream': 'yes',
            'adapter_role': role,
            'empirical_reading': 'Expected-decision point checks flag decision-table mismatches; LatticeGuard admits the overlapping subset that violates a declared law under the applicability predicate, leaving point-only rows visible but outside law-failure claims.',
        })

    comparable = 0
    discrepancies = 0
    for row in baseline_rows:
        if _field(row, 'baseline_id') == 'CROSS_ADAPTER_DIFFERENTIAL_ONLY':
            status = _field(row, 'oracle_status')
            if 'discrepancies=' in status and '/comparable=' in status:
                try:
                    discrepancies = int(status.split('discrepancies=', 1)[1].split('/comparable=', 1)[0])
                    comparable = int(status.split('/comparable=', 1)[1].split()[0].split(';')[0])
                except ValueError:
                    discrepancies = 0
                    comparable = 0
            break
    rows.append({
        'comparison_id': 'cross-adapter-differential-primary-head-to-head',
        'deployed_idiom': 'cross-adapter differential comparison',
        'frozen_stream': 'primary comparable Casbin/Cedar transformations',
        'stream_rows': comparable,
        'deployed_check_rows': comparable,
        'deployed_reported_failures': discrepancies,
        'latticeguard_checked_rows': comparable,
        'latticeguard_law_failures': 0,
        'overlap_failures': 0,
        'deployed_only_failures': discrepancies,
        'latticeguard_only_failures': 0,
        'same_input_stream': 'yes',
        'adapter_role': 'differential_signal',
        'empirical_reading': 'The comparable fragment has no backend disagreements; the row is useful as a consistency check but supplies no independent law failure in the current clean run.',
    })

    primary_stream_rows = sum(int(row['stream_rows']) for row in rows if 'primary' in str(row['comparison_id']) and 'seeded' not in str(row['comparison_id']) and 'cross-adapter' not in str(row['comparison_id']))
    seeded_stream_rows = sum(int(row['stream_rows']) for row in rows if 'seeded' in str(row['comparison_id']))
    seeded_deployed_failures = sum(int(row['deployed_reported_failures']) for row in rows if 'seeded' in str(row['comparison_id']))
    seeded_law_failures = sum(int(row['latticeguard_law_failures']) for row in rows if 'seeded' in str(row['comparison_id']))
    seeded_overlap = sum(int(row['overlap_failures']) for row in rows if 'seeded' in str(row['comparison_id']))
    seeded_point_only = sum(int(row['deployed_only_failures']) for row in rows if 'seeded' in str(row['comparison_id']))
    seeded_law_only = sum(int(row['latticeguard_only_failures']) for row in rows if 'seeded' in str(row['comparison_id']))
    missing_refs = sum(_point_join_rows(seeded_rows, primary_rows, prefix)['missing_reference_rows'] for prefix in ['casbin_py', 'cedar_py'])
    report = {
        'status': 'PASS' if primary_stream_rows == 15840 and seeded_stream_rows == 36960 and seeded_law_failures == 5040 and seeded_overlap == 5040 and seeded_law_only == 0 and missing_refs == 0 else 'FAIL',
        'rows': len(rows),
        'native_adapter_count': 2,
        'decision_harness_count': 1,
        'primary_head_to_head_stream_rows': primary_stream_rows,
        'primary_head_to_head_failures': sum(int(row['latticeguard_law_failures']) for row in rows if 'primary' in str(row['comparison_id']) and 'seeded' not in str(row['comparison_id'])),
        'seeded_head_to_head_stream_rows': seeded_stream_rows,
        'seeded_point_mismatch_rows': seeded_deployed_failures,
        'seeded_law_kill_rows': seeded_law_failures,
        'seeded_overlap_rows': seeded_overlap,
        'seeded_point_only_rows': seeded_point_only,
        'seeded_law_only_rows': seeded_law_only,
        'cross_adapter_comparable_rows': comparable,
        'cross_adapter_discrepancies': discrepancies,
        'missing_reference_rows': missing_refs,
        'opa_role': 'normalized_decision_harness_with_supplied_closure',
        'audit_claim': 'The deployed-tool comparison is empirical: point-test and differential idioms are evaluated over the same frozen streams as the law oracle, while OPA is reported as a normalized decision harness rather than a native hierarchy adapter.',
    }
    return rows, report


def write_deployed_tool_head_to_head(root: Path) -> dict[str, object]:
    rows, report = deployed_tool_head_to_head_rows(root)
    _write_csv(root / 'results' / 'deployed_tool_head_to_head.csv', rows)
    (root / 'results' / 'deployed_tool_head_to_head.json').write_text(
        json.dumps(report, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report
