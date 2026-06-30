from __future__ import annotations
import csv
from pathlib import Path

def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def slice_matrix(root: Path) -> list[dict]:
    rows=[r for r in read_csv(root/'results'/'obligations.csv') if r.get('oracle_status')=='PASS']
    out=[]
    for (adapter, rel), group in sorted(_group(rows, ('adapter_id','relation_id')).items()):
        sources=len({r['source_id'] for r in group})
        passes=sum(1 for r in group if r.get('oracle_status')=='PASS')
        out.append({'adapter_id':adapter,'relation_id':rel,'sources':sources,'obligations':len(group),'passes':passes,'status':'PASS' if passes==len(group) else 'FAIL'})
    return out

def _group(rows, keys):
    d={}
    for r in rows:
        key=tuple(r[k] for k in keys)
        d.setdefault(key,[]).append(r)
    return d
