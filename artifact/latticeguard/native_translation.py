from __future__ import annotations
import csv, json
from pathlib import Path

def parse_casbin_policy_csv(path: Path) -> list[dict[str,str]]:
    rows=[]
    with path.open('r', encoding='utf-8') as f:
        for raw in f:
            parts=[p.strip() for p in raw.strip().split(',')]
            if not parts or not parts[0]: continue
            if parts[0]=='p':
                rows.append({'kind':'policy','subject_or_role':parts[1], 'resource':parts[2], 'action':parts[3], 'effect':parts[4] if len(parts)>4 else 'allow'})
            if parts[0]=='g':
                rows.append({'kind':'role_edge','subject_or_role':parts[1], 'parent':parts[2], 'resource':'', 'action':'', 'effect':''})
    return rows

def parse_cedar_entities_json(path: Path) -> list[dict[str,str]]:
    data=json.loads(path.read_text(encoding='utf-8'))
    rows=[]
    for ent in data:
        uid=ent.get('uid',{})
        for parent in ent.get('parents',[]):
            rows.append({'child_type':uid.get('type',''), 'child_id':uid.get('id',''), 'parent_type':parent.get('type',''), 'parent_id':parent.get('id','')})
    return rows

def native_translation_digest(root: Path) -> list[dict[str,str]]:
    rows=[]
    for policy in sorted((root/'subjects'/'native_public').glob('*/policy.csv')):
        rows.append({'path':str(policy.relative_to(root)), 'parsed_rows':str(len(parse_casbin_policy_csv(policy))), 'family':'casbin'})
    for ent in sorted((root/'subjects'/'native_public').glob('*/entities.json')):
        rows.append({'path':str(ent.relative_to(root)), 'parsed_rows':str(len(parse_cedar_entities_json(ent))), 'family':'cedar'})
    return rows
