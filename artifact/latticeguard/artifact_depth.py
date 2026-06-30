from __future__ import annotations
import csv, json
from pathlib import Path

def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def compute_depth(root: Path) -> dict:
    res=root/'results'
    obligations=read_csv(res/'obligations.csv')
    pred=read_csv(res/'predicate_evaluations.csv')
    cex=json.loads((res/'counterexamples.json').read_text())
    model=json.loads((res/'model_check_summary.json').read_text())
    relation_ids=sorted({r['relation_id'] for r in obligations})
    sources=sorted({r['source_id'] for r in obligations})
    adapters=sorted({r['adapter_id'] for r in obligations})
    depth={
        'adapters': len(adapters), 'adapter_ids': adapters,
        'sources': len(sources), 'relations': len(relation_ids),
        'obligations': len(obligations), 'predicate_rows': len(pred),
        'counterexamples': len(cex),
        'bounded_model_cases': model.get('cases_checked', 0),
        'obligation_density': round(len(obligations)/(max(1,len(sources))*max(1,len(relation_ids))*max(1,len(adapters))), 3),
    }
    depth['repository_quality_thresholds']={
        'obligations>=1000': len(obligations)>=1000,
        'predicate_rows>=700': len(pred)>=700,
        'model_cases>=70000': model.get('cases_checked',0)>=70000,
        'density>=1.0': depth['obligation_density']>=1.0,
    }
    depth['status']='PASS' if all(depth['repository_quality_thresholds'].values()) else 'REVIEW'
    return depth
