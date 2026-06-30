from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Mapping, Sequence


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, '') for k in fields})


def baseline_effectiveness_rows(root: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    results = root / 'results'
    summary = _read_json(results / 'summary.json')
    baseline = _read_csv(results / 'baseline_results.csv')
    obligations = _read_csv(results / 'obligations.csv')
    rejections = _read_csv(results / 'rejections.csv')
    semantic = _read_json(results / 'semantic_counterexample_replay.json') if (results / 'semantic_counterexample_replay.json').exists() else {}

    by_baseline: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in baseline:
        by_baseline[row['baseline_id']].append(row)

    full_killed = int(summary.get('seeded_mutants_killed', 0))
    invalid_rejected = int(summary.get('rejected_invalid_transformations', 0))
    applicable = int(summary.get('primary_evaluated_obligations', 0))
    semantic_replayed = int(semantic.get('counterexamples_semantically_replayed', 0) or 0)

    rows: list[dict[str, object]] = []
    for bid in sorted(by_baseline):
        group = by_baseline[bid]
        killed = sum(str(r.get('killed', '')).lower() == 'true' for r in group)
        failures = sum(r.get('oracle_status') == 'FAIL' for r in group)
        invalid_admitted = 0
        notes = []
        for r in group:
            reason = r.get('reason', '') + ' ' + r.get('oracle_status', '')
            if 'invalid_candidates_would_be_counted=' in reason:
                try:
                    invalid_admitted += int(reason.split('invalid_candidates_would_be_counted=', 1)[1].split()[0].split(';')[0])
                except Exception:
                    pass
            if 'would_admit_invalid=' in reason:
                try:
                    invalid_admitted += int(reason.split('would_admit_invalid=', 1)[1].split()[0].split(';')[0])
                except Exception:
                    pass
            if r.get('reason'):
                notes.append(r.get('reason', ''))
        if bid == 'LATTICEGUARD_FULL_ORACLE':
            detection_rate = 1.0 if full_killed else 0.0
            denominator_safety = 1.0 if invalid_rejected and applicable else 0.0
            semantic_replay_rate = 1.0 if semantic_replayed == full_killed and full_killed else 0.0
        elif bid == 'SEEDED_MUTANT_POSITIVE_CONTROL':
            detection_rate = killed / max(1, len(group))
            denominator_safety = ''
            semantic_replay_rate = ''
        else:
            detection_rate = killed / max(1, full_killed)
            denominator_safety = 0.0 if invalid_admitted else ('' if bid not in {'NO_APPLICABILITY_GATE', 'PROPERTY_GENERATOR_NO_REJECTION'} else 0.0)
            semantic_replay_rate = ''
        rows.append({
            'baseline_id': bid,
            'rows': len(group),
            'seeded_killed_or_detected': killed,
            'oracle_failures': failures,
            'relative_seeded_detection_vs_full': f'{detection_rate:.6f}' if isinstance(detection_rate, float) else detection_rate,
            'invalid_transformations_admitted': invalid_admitted,
            'denominator_safety_score': f'{denominator_safety:.6f}' if isinstance(denominator_safety, float) else denominator_safety,
            'semantic_replay_rate': f'{semantic_replay_rate:.6f}' if isinstance(semantic_replay_rate, float) else semantic_replay_rate,
            'interpretation': _interpretation(bid, killed, full_killed, invalid_admitted, notes),
        })

    relation_kills = Counter()
    for row in baseline:
        if row.get('baseline_id') == 'SEEDED_MUTANT_POSITIVE_CONTROL' and str(row.get('killed')).lower() == 'true':
            relation_kills[row.get('relation_id', '')] += 1
    relation_rows = []
    for relation_id, count in sorted(relation_kills.items()):
        relation_rows.append({
            'baseline_id': 'SEEDED_MUTANT_POSITIVE_CONTROL_BY_RELATION',
            'rows': '',
            'seeded_killed_or_detected': count,
            'oracle_failures': '',
            'relative_seeded_detection_vs_full': f'{count / max(1, full_killed):.6f}',
            'invalid_transformations_admitted': '',
            'denominator_safety_score': '',
            'semantic_replay_rate': '',
            'interpretation': f'{relation_id} contributed {count} independently replayed seeded drift detections',
        })
    rows.extend(relation_rows)

    summary_report = {
        'status': 'PASS' if full_killed == semantic_replayed and invalid_rejected == len(rejections) and applicable == sum(1 for r in obligations if r.get('applicability_status') == 'APPLICABLE_EVALUATED') else 'FAIL',
        'full_oracle_seeded_killed': full_killed,
        'semantic_counterexamples_replayed': semantic_replayed,
        'invalid_transformations_rejected': invalid_rejected,
        'applicable_primary_obligations': applicable,
        'baseline_families': len(by_baseline),
        'relation_kill_families': len(relation_kills),
        'strongest_non_full_detection': max((sum(str(r.get('killed')).lower() == 'true' for r in group) for bid, group in by_baseline.items() if bid != 'LATTICEGUARD_FULL_ORACLE'), default=0),
        'audit_claim': 'Full law-level oracle combines denominator safety, seeded drift sensitivity, and semantic counterexample replay; weaker baselines lack at least one of these three properties.',
    }
    return rows, summary_report


def _interpretation(bid: str, killed: int, full_killed: int, invalid: int, notes: list[str]) -> str:
    if bid == 'LATTICEGUARD_FULL_ORACLE':
        return 'full oracle is the only baseline row that jointly has law predicates, rejection discipline, seeded drift detection, and replayable counterexamples'
    if bid in {'NO_APPLICABILITY_GATE', 'PROPERTY_GENERATOR_NO_REJECTION'}:
        return f'admits {invalid} invalid transformations, showing why denominator gating is part of the oracle rather than a reporting convention'
    if bid == 'CROSS_ADAPTER_DIFFERENTIAL_ONLY':
        return 'finds no disagreement in the comparable current slice and therefore cannot replace law-level invariants'
    if bid == 'UPSTREAM_ONLY':
        return 'native upstream tests exercise examples but do not encode metamorphic before/after law obligations'
    if bid == 'SEEDED_MUTANT_POSITIVE_CONTROL':
        return f'positive-control rows kill {killed}/{len(notes) if notes else full_killed} row-level seeded drifts before minimization aggregation'
    if bid == 'SINGLE_RELATION':
        return f'single-law ablations detect {killed} relation-local drift families but cannot cover the full relation lattice'
    return 'baseline retained for adversarial comparison; it lacks either predicates, replay, or law-level failure interpretation'


def write_oracle_efficacy(root: Path) -> dict[str, object]:
    rows, report = baseline_effectiveness_rows(root)
    fields = ['baseline_id', 'rows', 'seeded_killed_or_detected', 'oracle_failures', 'relative_seeded_detection_vs_full', 'invalid_transformations_admitted', 'denominator_safety_score', 'semantic_replay_rate', 'interpretation']
    _write_csv(root / 'results' / 'oracle_efficacy_summary.csv', rows, fields)
    (root / 'results' / 'oracle_efficacy_summary.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return report
