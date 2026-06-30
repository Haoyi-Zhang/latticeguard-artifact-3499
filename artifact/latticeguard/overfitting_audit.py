from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
from typing import Any


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def _split(source_id: str) -> str:
    # Deterministic source-level split independent of result outcomes.  Roughly
    # one third of sources become holdout; the decision uses only the source ID.
    b = hashlib.sha256(source_id.encode('utf-8')).digest()[0]
    return 'holdout' if b < 96 else 'development'


def build_overfitting_audit(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results = root / 'results'
    obligations = _read_csv(results / 'obligations.csv')
    predicates = _read_csv(results / 'predicate_evaluations.csv')
    source_manifest = _read_csv(root / 'source_manifest.csv')

    stratum_by_source = {r.get('source_id',''): r.get('kind','') + ':' + r.get('notes','')[:60] for r in source_manifest}
    pred_by_source: dict[str, list[dict[str, str]]] = {}
    for r in predicates:
        pred_by_source.setdefault(r['source_id'], []).append(r)

    rows: list[dict[str, Any]] = []
    for source_id in sorted({r['source_id'] for r in obligations}):
        rs = [r for r in obligations if r['source_id'] == source_id]
        pr = pred_by_source.get(source_id, [])
        evaluated = [r for r in rs if r.get('applicability_status') == 'APPLICABLE_EVALUATED']
        rejected = [r for r in rs if r.get('applicability_status') == 'REJECTED_NOT_COUNTED']
        unsupported = [r for r in rs if r.get('applicability_status') == 'UNSUPPORTED_NOT_COUNTED']
        rows.append({
            'source_id': source_id,
            'split': _split(source_id),
            'source_manifest_kind': stratum_by_source.get(source_id, 'missing_manifest_row'),
            'adapter_count': len({r['adapter_id'] for r in evaluated}),
            'relation_count': len({r['relation_id'] for r in evaluated}),
            'evaluated_obligations': len(evaluated),
            'rejected_rows': len(rejected),
            'unsupported_rows': len(unsupported),
            'predicate_candidates': len(pr),
            'predicate_witness_hashes': len({r.get('witness_hash','') for r in pr}),
            'candidate_shape_families': len({r['candidate_id'].split(':', 1)[-1] if ':' in r['candidate_id'] else r['candidate_id'] for r in rs}),
            'status': 'PASS' if len({r['relation_id'] for r in evaluated}) == 12 and len({r['adapter_id'] for r in evaluated}) >= 2 and len(evaluated) > 0 else 'FAIL',
        })

    holdout = [r for r in rows if r['split'] == 'holdout']
    dev = [r for r in rows if r['split'] == 'development']
    holdout_obligations = [r for r in obligations if _split(r['source_id']) == 'holdout' and r.get('applicability_status') == 'APPLICABLE_EVALUATED']
    dev_obligations = [r for r in obligations if _split(r['source_id']) == 'development' and r.get('applicability_status') == 'APPLICABLE_EVALUATED']
    report = {
        'status': 'PASS',
        'source_split_rule': 'sha256(source_id)[0] < 96 => holdout; outcome-independent',
        'sources_total': len(rows),
        'holdout_sources': len(holdout),
        'development_sources': len(dev),
        'holdout_evaluated_obligations': len(holdout_obligations),
        'development_evaluated_obligations': len(dev_obligations),
        'holdout_relation_count': len({r['relation_id'] for r in holdout_obligations}),
        'holdout_adapter_count': len({r['adapter_id'] for r in holdout_obligations}),
        'holdout_passes': sum(1 for r in holdout_obligations if r.get('oracle_status') == 'PASS'),
        'holdout_failures': sum(1 for r in holdout_obligations if r.get('oracle_status') == 'FAIL'),
        'development_failures': sum(1 for r in dev_obligations if r.get('oracle_status') == 'FAIL'),
        'per_source_rows_failing_audit': sum(1 for r in rows if r['status'] != 'PASS'),
        'interpretation': 'Checks whether evidence survives an outcome-independent held-out source split; this is not a statistical generalization claim.',
    }
    errors=[]
    if len(holdout) < max(5, len(rows)//8): errors.append('too few holdout sources')
    if report['holdout_relation_count'] != 12: errors.append('holdout does not cover all relation families')
    if report['holdout_adapter_count'] < 2: errors.append('holdout does not cover both counted adapters')
    if report['per_source_rows_failing_audit'] != 0: errors.append('one or more sources fails per-source audit')
    if report['holdout_evaluated_obligations'] < 500: errors.append('holdout obligation count below robustness threshold')
    report['errors'] = errors
    if errors:
        report['status'] = 'FAIL'
    return rows, report
