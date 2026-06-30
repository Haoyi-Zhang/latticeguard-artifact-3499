from __future__ import annotations

import csv, json, hashlib
from pathlib import Path
from typing import Any

INDEXED_EXTENSIONS={'.py','.md','.tex','.bib','.csv','.json','.cff','.txt','.conf','.cedar'}

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def classify(path: Path) -> str:
    parts=set(path.parts)
    if 'scripts' in parts: return 'script'
    if 'latticeguard' in parts: return 'library'
    if 'tests' in parts: return 'unit_test'
    if 'results' in parts: return 'result'
    if 'subjects' in parts: return 'subject'
    if 'evidence' in parts: return 'evidence'
    if path.name.endswith('.tex') or path.name.endswith('.bib'): return 'paper'
    return 'metadata'


def build_artifact_index(repo_root: Path) -> list[dict[str,str]]:
    rows=[]
    for path in repo_root.rglob('*'):
        if not path.is_file(): continue
        if '__pycache__' in path.parts or path.suffix == '.pyc': continue
        if path.suffix.lower() not in INDEXED_EXTENSIONS: continue
        rel=str(path.relative_to(repo_root))
        rows.append({'path':rel,'class':classify(path),'bytes':str(path.stat().st_size),'sha256':sha256_file(path)})
    rows.sort(key=lambda r:r['path'])
    return rows


def write_artifact_index(repo_root: Path, out: Path) -> list[dict[str,str]]:
    rows=build_artifact_index(repo_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=['path','class','bytes','sha256']); w.writeheader(); w.writerows(rows)
    return rows


def summarize_index(rows: list[dict[str,str]]) -> dict[str, Any]:
    counts={}
    for r in rows:
        counts[r['class']]=counts.get(r['class'],0)+1
    return {'files':len(rows),'classes':counts,'bytes':sum(int(r['bytes']) for r in rows)}
