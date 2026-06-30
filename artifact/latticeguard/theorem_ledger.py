from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

RELATION_THEOREMS = [
    {
        'relation_id': 'DD',
        'theorem_id': 'T-DD-default-deny-preservation',
        'statement': 'Adding material that remains unreachable from the request slice preserves default deny.',
        'core_side_condition': 'No reachable matching allow or deny exists before or after the transformation.',
        'missing_side_condition_counterexample': 'A newly reachable allow changes DENY to ALLOW.',
    },
    {
        'relation_id': 'DO',
        'theorem_id': 'T-DO-deny-dominance',
        'statement': 'A newly added matching deny dominates an existing matching allow under deny-overrides composition.',
        'core_side_condition': 'The added deny matches the same principal/action/resource closure as the allow witness.',
        'missing_side_condition_counterexample': 'A deny on an unrelated role or resource does not dominate the request.',
    },
    {
        'relation_id': 'PA',
        'theorem_id': 'T-PA-deny-aware-principal-monotonicity',
        'statement': 'Allow is preserved under principal substitution to a role-closure superset only when the follow-up slice adds no matching deny.',
        'core_side_condition': 'After closure is a superset of before closure and no newly reachable deny matches the request.',
        'missing_side_condition_counterexample': 'The substituted principal inherits a denied role and ALLOW changes to DENY.',
    },
    {
        'relation_id': 'DA',
        'theorem_id': 'T-DA-deny-antitonicity',
        'statement': 'A denied request remains denied when the deny witness remains reachable after principal substitution.',
        'core_side_condition': 'At least one matching deny witness is reachable in the follow-up policy/request pair.',
        'missing_side_condition_counterexample': 'Substitution loses the denied role and exposes only an allow or default-deny case.',
    },
    {
        'relation_id': 'IE',
        'theorem_id': 'T-IE-irrelevant-extension',
        'statement': 'Adding policy material outside the request-reachable slice preserves the decision.',
        'core_side_condition': 'No added rule, role, action, or resource becomes reachable from the request slice.',
        'missing_side_condition_counterexample': 'A syntactically new rule is semantically reachable and changes the decision.',
    },
    {
        'relation_id': 'ID',
        'theorem_id': 'T-ID-idempotent-rule-duplication',
        'statement': 'Duplicating a semantically identical rule preserves the deny-overrides decision.',
        'core_side_condition': 'The duplicate has the same effect, role, action, and resource as an existing rule.',
        'missing_side_condition_counterexample': 'Changing any semantic field makes the duplicate a new rule rather than an idempotent copy.',
    },
    {
        'relation_id': 'HC',
        'theorem_id': 'T-HC-hierarchy-closure',
        'statement': 'Materializing an already implied hierarchy edge preserves every request decision in the slice.',
        'core_side_condition': 'The inserted edge is already present in the transitive closure relevant to the request.',
        'missing_side_condition_counterexample': 'A non-implied edge expands reachability and may expose an allow or deny.',
    },
    {
        'relation_id': 'HR',
        'theorem_id': 'T-HR-hierarchy-refactoring',
        'statement': 'Rewriting an assignment to a fresh child role preserves the decision when the child inherits the replaced role set.',
        'core_side_condition': 'The new child role inherits all roles that made the original request slice observable.',
        'missing_side_condition_counterexample': 'A child role missing a parent loses an allow or deny witness.',
    },
    {
        'relation_id': 'SR',
        'theorem_id': 'T-SR-shadowed-allow-removal',
        'statement': 'Removing an allow shadowed by a matching deny preserves deny.',
        'core_side_condition': 'A matching deny remains after removing the allow.',
        'missing_side_condition_counterexample': 'Removing an unshadowed allow changes ALLOW to DENY.',
    },
    {
        'relation_id': 'RO',
        'theorem_id': 'T-RO-unordered-rule-permutation',
        'statement': 'Permuting rules preserves decisions in an unordered deny-overrides fragment.',
        'core_side_condition': 'The fragment has no priority, first-match, last-match, or ordered effect semantics.',
        'missing_side_condition_counterexample': 'Priority semantics can make the first matching rule decisive.',
    },
    {
        'relation_id': 'AR',
        'theorem_id': 'T-AR-off-slice-alpha-renaming',
        'statement': 'An injective renaming outside the request-reachable slice preserves the decision.',
        'core_side_condition': 'The rename does not touch the requested principal, action, resource, or any reachable witness.',
        'missing_side_condition_counterexample': 'Renaming the queried resource changes which rules match.',
    },
    {
        'relation_id': 'SM',
        'theorem_id': 'T-SM-scope-split-merge',
        'statement': 'Splitting a permission scope preserves the target request when the matched action/resource assignment is preserved.',
        'core_side_condition': 'The target request has an equivalent matching allow after the split and no deny interference is introduced.',
        'missing_side_condition_counterexample': 'A split that omits the target action or resource drops the allow witness.',
    },
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, '') for key in fieldnames})


def theorem_rows(root: Path) -> list[dict[str, object]]:
    results = root / 'results'
    soundness = _read_csv(results / 'soundness_checks.csv')
    contracts = _read_csv(results / 'relation_contracts.csv')
    model_summary = json.loads((results / 'model_check_summary.json').read_text(encoding='utf-8')) if (results / 'model_check_summary.json').exists() else {}
    sound_count = Counter(row.get('relation_id', '') for row in soundness if row.get('soundness_check') == 'PASS')
    fail_count = Counter(row.get('relation_id', '') for row in soundness if row.get('soundness_check') != 'PASS')
    contract_ids = {row.get('relation_id', '') for row in contracts}
    model_counts = model_summary.get('relation_counts', {}) if isinstance(model_summary, dict) else {}
    rows: list[dict[str, object]] = []
    for theorem in RELATION_THEOREMS:
        rel = theorem['relation_id']
        rows.append({
            **theorem,
            'contract_present': str(rel in contract_ids).lower(),
            'predicate_soundness_rows': sound_count.get(rel, 0),
            'predicate_soundness_failures': fail_count.get(rel, 0),
            'bounded_model_cases': model_counts.get(rel, 0),
            'proof_artifact': 'relation_contracts.csv;soundness_checks.csv;model_check_cases.csv;proof_certificate.json',
            'status': 'PASS' if rel in contract_ids and fail_count.get(rel, 0) == 0 and int(model_counts.get(rel, 0)) > 0 else 'FAIL',
        })
    return rows


def proof_obligation_rows(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in theorem_rows(root):
        rel = row['relation_id']
        for obligation, evidence, status in [
            ('contract_exists', 'relation_contracts.csv', row['contract_present'] == 'true'),
            ('predicate_witnesses_sound', 'soundness_checks.csv', int(row['predicate_soundness_failures']) == 0 and int(row['predicate_soundness_rows']) > 0),
            ('bounded_core_covered', 'model_check_cases.csv', int(row['bounded_model_cases']) > 0),
            ('counterexample_side_condition_documented', 'theorem_ledger.csv', bool(row['missing_side_condition_counterexample'])),
        ]:
            rows.append({
                'relation_id': rel,
                'theorem_id': row['theorem_id'],
                'proof_obligation': obligation,
                'evidence_file': evidence,
                'status': 'PASS' if status else 'FAIL',
            })
    return rows


def write_theorem_ledgers(root: Path) -> dict[str, object]:
    rows = theorem_rows(root)
    obligations = proof_obligation_rows(root)
    theorem_fields = [
        'relation_id', 'theorem_id', 'statement', 'core_side_condition',
        'missing_side_condition_counterexample', 'contract_present',
        'predicate_soundness_rows', 'predicate_soundness_failures',
        'bounded_model_cases', 'proof_artifact', 'status'
    ]
    obligation_fields = ['relation_id', 'theorem_id', 'proof_obligation', 'evidence_file', 'status']
    _write_csv(root / 'results' / 'theorem_ledger.csv', rows, theorem_fields)
    _write_csv(root / 'results' / 'theorem_obligations.csv', obligations, obligation_fields)
    failures = [row for row in rows if row.get('status') != 'PASS'] + [row for row in obligations if row.get('status') != 'PASS']
    return {
        'status': 'PASS' if not failures and len(rows) == 12 and len(obligations) == 48 else 'FAIL',
        'theorems': len(rows),
        'proof_obligations': len(obligations),
        'failures': len(failures),
    }
