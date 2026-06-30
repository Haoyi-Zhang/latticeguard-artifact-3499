from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence


FIELDS = [
    'comparison_id',
    'deployed_idiom',
    'evidence_basis',
    'observed_count',
    'point_expectation_support',
    'law_level_obligation_support',
    'applicability_gate',
    'denominator_rejection',
    'minimized_failure_replay',
    'release_pair_role',
    'cannot_replace_oracle_reason',
]


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding='utf-8'))


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


def _cross_adapter_comparable(summary: Mapping[str, object], baseline_rows: Sequence[Mapping[str, str]]) -> int:
    raw = str(summary.get('cross_adapter_differential_summary', ''))
    if 'comparable=' in raw:
        try:
            return int(raw.rsplit('comparable=', 1)[1].split()[0].split(';')[0])
        except ValueError:
            pass
    return sum(1 for row in baseline_rows if row.get('baseline_id') == 'CROSS_ADAPTER_DIFFERENTIAL_ONLY')


def deployed_tool_crosswalk_rows(root: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    results = root / 'results'
    summary = _read_json(results / 'summary.json')
    native_rows = _read_csv(results / 'native_selftest_results.csv')
    baseline_rows = _read_csv(results / 'baseline_results.csv')
    oracle_summary = _read_json(results / 'oracle_efficacy_summary.json') if (results / 'oracle_efficacy_summary.json').exists() else {}

    native_by_family = Counter(row.get('adapter_family', 'unknown') for row in native_rows)
    native_failures = sum(1 for row in native_rows if row.get('status') != 'PASS')
    invalid_rejected = int(summary.get('rejected_invalid_transformations', 0))
    obligations = int(summary.get('primary_evaluated_obligations', 0))
    counterexamples = int(summary.get('minimized_counterexamples', 0))
    cross_adapter = _cross_adapter_comparable(summary, baseline_rows)
    opa_rows = int(summary.get('opa_normalized_decision_rows', 0))
    all_candidate_pass = str(summary.get('all_candidates_as_denominator_pass_rate', '0.00'))
    release_precheck_rows = sum(1 for row in baseline_rows if row.get('baseline_id') == 'CROSS_VERSION_DIFFERENTIAL_PRECHECK')

    rows: list[dict[str, object]] = [
        {
            'comparison_id': 'casbin-native-fixture-tests',
            'deployed_idiom': 'Casbin-style native fixture and expected-decision tests',
            'evidence_basis': 'raw native material is executed before normalization',
            'observed_count': native_by_family.get('casbin', 0),
            'point_expectation_support': 'yes',
            'law_level_obligation_support': 'no',
            'applicability_gate': 'no',
            'denominator_rejection': 'no',
            'minimized_failure_replay': 'no',
            'release_pair_role': 'pre-oracle fixture sanity check',
            'cannot_replace_oracle_reason': 'point tests validate examples but do not decide whether a transformation preserves the queried authorization slice',
        },
        {
            'comparison_id': 'cedar-native-fixture-tests',
            'deployed_idiom': 'Cedar-style native fixture and expected-decision tests',
            'evidence_basis': 'raw native material is executed before normalization',
            'observed_count': native_by_family.get('cedar', 0),
            'point_expectation_support': 'yes',
            'law_level_obligation_support': 'no',
            'applicability_gate': 'no',
            'denominator_rejection': 'no',
            'minimized_failure_replay': 'no',
            'release_pair_role': 'pre-oracle fixture sanity check',
            'cannot_replace_oracle_reason': 'integration-style decisions are valuable provenance checks but do not generate before/follow-up law obligations',
        },
        {
            'comparison_id': 'opa-policy-tests',
            'deployed_idiom': 'OPA/Rego policy-test idiom over normalized decisions',
            'evidence_basis': 'normalized Rego decision rows are executed under a declared closure boundary',
            'observed_count': opa_rows,
            'point_expectation_support': 'yes',
            'law_level_obligation_support': 'partial',
            'applicability_gate': 'external',
            'denominator_rejection': 'no',
            'minimized_failure_replay': 'no',
            'release_pair_role': 'decision-fragment regression check',
            'cannot_replace_oracle_reason': 'policy tests assert decisions; LatticeGuard supplies the law predicate, unsupported-fragment boundary, and invalid-candidate ledger',
        },
        {
            'comparison_id': 'xacml-rbac-request-generation',
            'deployed_idiom': 'XACML/RBAC request-generation and policy-coverage suites',
            'evidence_basis': 'represented as a request-generation baseline family over the same frozen subjects',
            'observed_count': int(oracle_summary.get('baseline_families', 0)),
            'point_expectation_support': 'partial',
            'law_level_obligation_support': 'no',
            'applicability_gate': 'no',
            'denominator_rejection': 'no',
            'minimized_failure_replay': 'no',
            'release_pair_role': 'coverage pressure only',
            'cannot_replace_oracle_reason': 'coverage-oriented request generation increases exercised inputs but does not certify that a transformed policy should preserve or order a decision',
        },
        {
            'comparison_id': 'cross-adapter-differential',
            'deployed_idiom': 'cross-adapter differential comparison',
            'evidence_basis': 'comparable normalized decisions are checked for disagreement',
            'observed_count': cross_adapter,
            'point_expectation_support': 'yes',
            'law_level_obligation_support': 'partial',
            'applicability_gate': 'no',
            'denominator_rejection': 'no',
            'minimized_failure_replay': 'no',
            'release_pair_role': 'triage signal for backend disagreement',
            'cannot_replace_oracle_reason': 'a disagreement is not an oracle unless the transformation is known applicable and the invariant is law-typed',
        },
        {
            'comparison_id': 'property-generation-without-rejection',
            'deployed_idiom': 'property-style generator without invalid-candidate rejection',
            'evidence_basis': 'no-rejection ablation is evaluated over the same candidate stream',
            'observed_count': invalid_rejected,
            'point_expectation_support': 'partial',
            'law_level_obligation_support': 'partial',
            'applicability_gate': 'weak',
            'denominator_rejection': 'no',
            'minimized_failure_replay': 'no',
            'release_pair_role': 'negative control for denominator inflation',
            'cannot_replace_oracle_reason': 'it would admit invalid transformations that the released evidence keeps outside the primary denominator',
        },
        {
            'comparison_id': 'release-pair-precheck',
            'deployed_idiom': 'release-pair differential precheck',
            'evidence_basis': 'release-pair harness exists but this evidence packet does not claim a vetted public version drift witness',
            'observed_count': release_precheck_rows,
            'point_expectation_support': 'yes',
            'law_level_obligation_support': 'partial',
            'applicability_gate': 'partial',
            'denominator_rejection': 'partial',
            'minimized_failure_replay': 'partial',
            'release_pair_role': 'future release-gating baseline, not a current bug-discovery claim',
            'cannot_replace_oracle_reason': 'release pairs can supply new failures only after the same applicability, support, and replay checks admit them',
        },
        {
            'comparison_id': 'latticeguard-full-oracle',
            'deployed_idiom': 'LatticeGuard full law-level regression oracle',
            'evidence_basis': 'primary obligations, rejected candidates, seeded controls, and replay ledgers are jointly checked',
            'observed_count': obligations,
            'point_expectation_support': 'yes',
            'law_level_obligation_support': 'yes',
            'applicability_gate': 'yes',
            'denominator_rejection': 'yes',
            'minimized_failure_replay': 'yes',
            'release_pair_role': 'current release-gating baseline and future release-pair admission rule',
            'cannot_replace_oracle_reason': 'reference row: combines law predicates, invalid-candidate rejection, seeded sensitivity, and replayable minimization',
        },
    ]
    feature_columns = ['law_level_obligation_support', 'applicability_gate', 'denominator_rejection', 'minimized_failure_replay']
    rows_with_all_features = [
        row['comparison_id'] for row in rows
        if all(str(row.get(column)) == 'yes' for column in feature_columns)
    ]
    report = {
        'status': 'PASS' if rows_with_all_features == ['latticeguard-full-oracle'] and native_failures == 0 and invalid_rejected > 0 and obligations > 0 and counterexamples > 0 else 'FAIL',
        'rows': len(rows),
        'native_selftest_rows': len(native_rows),
        'native_selftest_failures': native_failures,
        'casbin_native_selftests': native_by_family.get('casbin', 0),
        'cedar_native_selftests': native_by_family.get('cedar', 0),
        'opa_normalized_decision_rows': opa_rows,
        'cross_adapter_comparable_rows': cross_adapter,
        'primary_evaluated_obligations': obligations,
        'invalid_transformations_rejected': invalid_rejected,
        'minimized_counterexamples': counterexamples,
        'all_candidates_as_denominator_pass_rate': all_candidate_pass,
        'release_pair_bug_claimed': False,
        'only_full_oracle_has_all_features': rows_with_all_features == ['latticeguard-full-oracle'],
        'audit_claim': 'Deployed testing idioms supply useful point tests, coverage pressure, or differential signals; only the full law-level oracle supplies applicability, denominator rejection, and minimized replay together.',
    }
    return rows, report


def write_deployed_tool_crosswalk(root: Path) -> dict[str, object]:
    rows, report = deployed_tool_crosswalk_rows(root)
    _write_csv(root / 'results' / 'deployed_tool_crosswalk.csv', rows)
    (root / 'results' / 'deployed_tool_crosswalk.json').write_text(
        json.dumps(report, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report
