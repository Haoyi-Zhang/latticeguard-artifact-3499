from __future__ import annotations
import csv
from pathlib import Path
RELATIONS=['DD','DO','PA','DA','IE','ID','HC','HR','SR','RO','AR','SM']
def coverage_rows(root: Path) -> list[dict[str,str]]:
    with (root/'results'/'obligations.csv').open('r', encoding='utf-8', newline='') as f: obs=list(csv.DictReader(f))
    cells={(r['adapter_id'],r['source_id'],r['relation_id']) for r in obs if r.get('applicability_status')=='APPLICABLE_EVALUATED'}
    adapters=sorted({a for a,_,_ in cells}); sources=sorted({s for _,s,_ in cells})
    return [{'adapter_id':a,'source_id':s,'relation_id':rel,'covered':str((a,s,rel) in cells).lower()} for a in adapters for s in sources for rel in RELATIONS]
def density(rows:list[dict[str,str]]) -> float: return sum(r['covered']=='true' for r in rows)/len(rows) if rows else 0.0
