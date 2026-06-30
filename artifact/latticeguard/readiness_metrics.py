from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

@dataclass(frozen=True)
class ReadinessDimension:
    name: str
    score: int
    weight: int
    evidence: str
    explanation: str

@dataclass(frozen=True)
class ReadinessReport:
    weighted_score: float
    dimensions: tuple[ReadinessDimension, ...]
    blockers: tuple[str, ...]
    recommendation: str


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def _count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open('r', encoding='utf-8', newline='') as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _score_threshold(value: int, thresholds: tuple[int, int, int, int]) -> int:
    low, mid, high, excellent = thresholds
    if value >= excellent:
        return 100
    if value >= high:
        return 90
    if value >= mid:
        return 75
    if value >= low:
        return 55
    return 25


def replay_dimension(root: Path) -> ReadinessDimension:
    summary = _read_json(root / 'results' / 'summary.json')
    obligations = int(summary.get('primary_evaluated_obligations', 0))
    failures = int(summary.get('primary_real_failures', 1))
    errors = int(summary.get('primary_errors', 1))
    score = _score_threshold(obligations, (72, 168, 408, 576))
    if failures or errors:
        score = min(score, 40)
    return ReadinessDimension('replay', score, 18, 'results/summary.json', f'{obligations} applicable primary obligations; failures={failures}; errors={errors}')


def predicate_dimension(root: Path) -> ReadinessDimension:
    rows = _count_csv(root / 'results' / 'predicate_evaluations.csv')
    soundness = _count_csv(root / 'results' / 'soundness_checks.csv')
    score = min(_score_threshold(rows, (119, 289, 408, 408)), _score_threshold(soundness, (119, 289, 408, 408)))
    return ReadinessDimension('applicability_predicates', score, 16, 'results/predicate_evaluations.csv', f'{rows} predicate rows and {soundness} reference-soundness rows')


def benchmark_dimension(root: Path) -> ReadinessDimension:
    summary = _read_json(root / 'results' / 'summary.json')
    sources = int(summary.get('source_ids_covered', 0))
    native = int(summary.get('native_selftest_rows', 0))
    upstream_audit = _count_csv(root / 'results' / 'upstream_benchmark_audit.csv')
    score = min(_score_threshold(sources, (7, 17, 24, 24)), _score_threshold(native, (20, 40, 67, 67)))
    if upstream_audit < 17:
        score = min(score, 85)
    return ReadinessDimension('benchmark_provenance', score, 16, 'results/upstream_benchmark_audit.csv', f'{sources} sources; {native} native selftest rows; {upstream_audit} audited native bundles')


def theory_dimension(root: Path) -> ReadinessDimension:
    model = _read_json(root / 'results' / 'model_check_summary.json')
    cases = int(model.get('cases_checked', 0))
    failures = int(model.get('failures', 1))
    relations = int(model.get('relations_covered', 0))
    score = _score_threshold(cases, (1000, 10000, 74024, 74024))
    if failures or relations < 12:
        score = min(score, 40)
    return ReadinessDimension('formal_core', score, 14, 'results/model_check_summary.json', f'{cases} bounded semantic cases; failures={failures}; relations={relations}')


def counterexample_dimension(root: Path) -> ReadinessDimension:
    summary = _read_json(root / 'results' / 'summary.json')
    counterexamples = int(summary.get('minimized_counterexamples', 0))
    rows = _count_csv(root / 'results' / 'counterexample_family_matrix.csv')
    score = min(_score_threshold(counterexamples, (30, 100, 170, 240)), _score_threshold(rows, (5, 8, 10, 10)))
    return ReadinessDimension('counterexample_replay', score, 12, 'results/counterexamples.json', f'{counterexamples} minimized seeded counterexamples; {rows} family-matrix rows')


def hygiene_dimension(root: Path) -> ReadinessDimension:
    scorecard = _read_json(root / 'results' / 'repository_scorecard.json')
    status = scorecard.get('status', 'FAIL')
    blockers = scorecard.get('blockers', [])
    score = 100 if status == 'PASS' and not blockers else 40
    return ReadinessDimension('hygiene', score, 10, 'results/repository_scorecard.json', f'scorecard={status}; blockers={len(blockers)}')


def github_dimension(root: Path) -> ReadinessDimension:
    rows = _count_csv(root / 'results' / 'github_sync_manifest.csv')
    score = _score_threshold(rows, (100, 500, 2000, 9000))
    return ReadinessDimension('github_sync_manifest', score, 6, 'results/github_sync_manifest.csv', f'{rows} repository paths classified for GitHub synchronization')


def gate_dimension(root: Path) -> ReadinessDimension:
    rows = _count_csv(root / 'results' / 'audit_objection_matrix.csv')
    score = _score_threshold(rows, (4, 6, 7, 7))
    return ReadinessDimension('audit_attack_surface', score, 8, 'results/audit_objection_matrix.csv', f'{rows} audit objections mapped to evidence files')


def dimensions(root: Path) -> tuple[ReadinessDimension, ...]:
    return (
        replay_dimension(root),
        predicate_dimension(root),
        benchmark_dimension(root),
        theory_dimension(root),
        counterexample_dimension(root),
        hygiene_dimension(root),
        github_dimension(root),
        gate_dimension(root),
    )


def compute_readiness(root: Path) -> ReadinessReport:
    dims = dimensions(root)
    total_weight = sum(d.weight for d in dims)
    weighted = sum(d.score * d.weight for d in dims) / total_weight if total_weight else 0.0
    blockers = tuple(f'{d.name}: score {d.score}' for d in dims if d.score < 75)
    if blockers:
        recommendation = 'repair-blockers-before-submission'
    elif weighted >= 95:
        recommendation = 'repository-ready-under-current-evidence-scope'
    else:
        recommendation = 'strong-but-continue-deepening'
    return ReadinessReport(weighted, dims, blockers, recommendation)


def report_dict(report: ReadinessReport) -> dict:
    return {
        'weighted_score': round(report.weighted_score, 2),
        'recommendation': report.recommendation,
        'blockers': list(report.blockers),
        'dimensions': [d.__dict__ for d in report.dimensions],
    }


def write_readiness_report(root: Path, output: Path) -> dict:
    report = compute_readiness(root)
    data = report_dict(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return data
