from __future__ import annotations
import csv
from pathlib import Path

EXPECTED_STRATA={'public_official_example_slice','public_native_import_slice','project_generated_law_probe'}

def corpus_audit(root: Path) -> dict[str,object]:
    with (root/'source_manifest.csv').open('r',encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    subject_rows=[r for r in rows if r.get('kind')=='subject_seed']
    native_rows=[r for r in rows if r.get('kind')=='native_public_fixture']
    errors=[]
    if len(subject_rows)<17: errors.append('subject corpus below target')
    if len(native_rows)<20: errors.append('native raw fixture files below target')
    for r in rows:
        if not r.get('license'): errors.append('missing license '+r.get('source_id','?'))
        if not r.get('sha256'): errors.append('missing sha256 '+r.get('source_id','?'))
    return {'status':'PASS' if not errors else 'FAIL','subject_rows':len(subject_rows),'native_files':len(native_rows),'errors':errors}

def inclusion_funnel(root: Path) -> list[dict[str,str]]:
    with (root/'source_manifest.csv').open('r',encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    out=[]
    for r in rows:
        if r.get('kind') in {'subject_seed','native_public_fixture'}:
            out.append({'source_id':r['source_id'],'decision':'included','reason':'offline deterministic source with license/hash/provenance','kind':r['kind']})
    return sorted(out,key=lambda r:(r['kind'],r['source_id']))
