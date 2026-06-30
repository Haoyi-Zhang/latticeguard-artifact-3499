from __future__ import annotations
import csv
from pathlib import Path

def build_funnel(root: Path) -> list[dict[str,str]]:
    rows=[]
    with (root/'source_manifest.csv').open('r', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            kind=r.get('kind','')
            if kind in {'subject_seed','native_public_fixture'}:
                rows.append({'source_id':r['source_id'],'kind':kind,'license':r.get('license',''),'hash_present':str(bool(r.get('sha256'))).lower(),'included':'true','reason':'public/offline deterministic source with license/hash/provenance'})
    rows.sort(key=lambda r:(r['kind'],r['source_id']))
    return rows
