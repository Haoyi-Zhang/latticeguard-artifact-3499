from __future__ import annotations
import csv, json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open('r', encoding='utf-8', newline='') as f: return list(csv.DictReader(f))


def summarize_evidence(root: Path) -> dict[str, Any]:
    results=root/'results'
    summary=json.loads((results/'summary.json').read_text(encoding='utf-8'))
    obligations=read_csv(results/'obligations.csv')
    pred=read_csv(results/'predicate_evaluations.csv')
    sound=read_csv(results/'soundness_checks.csv')
    native=read_csv(results/'native_selftest_results.csv')
    sources=read_csv(root/'source_manifest.csv')
    return {
        'adapters': sorted(set(r['adapter_id'] for r in obligations if r.get('applicability_status')=='APPLICABLE_EVALUATED')),
        'sources': int(summary.get('source_ids_covered',0)),
        'benchmark_sources': len([r for r in sources if r.get('kind') in {'subject_seed','native_public_fixture'}]),
        'native_benchmark_sources': len({r['source_id'].rsplit('_',1)[0] for r in sources if r.get('kind')=='native_public_fixture'}),
        'relations': sorted(set(r['relation_id'] for r in obligations if r.get('relation_id'))),
        'evaluated_obligations': int(summary.get('primary_evaluated_obligations',0)),
        'passes': int(summary.get('primary_passes',0)),
        'failures': int(summary.get('primary_real_failures',0)),
        'rejected': int(summary.get('rejected_invalid_transformations',0)),
        'unsupported': int(summary.get('unsupported_transformations',0)),
        'predicate_rows': len(pred),
        'soundness_rows': len(sound),
        'soundness_failures': len([r for r in sound if r.get('soundness_check')!='PASS' or (r.get('applicability_status')=='APPLICABLE_EVALUATED' and r.get('reference_oracle_status')!='PASS')]),
        'model_check_cases': int(summary.get('bounded_model_checked_cases',0)),
        'model_check_failures': int(summary.get('bounded_model_check_failures',0)),
        'native_selftests': len(native),
        'native_selftest_failures': len([r for r in native if r.get('status')!='PASS']),
    }
