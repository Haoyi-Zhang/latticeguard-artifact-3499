from __future__ import annotations
import json, csv
from collections import Counter
from pathlib import Path

def family_matrix(root: Path) -> list[dict[str,str]]:
    rows=json.loads((root/'results'/'counterexamples.json').read_text(encoding='utf-8'))
    c=Counter((r['adapter_id'], r['relation_id']) for r in rows)
    return [{'adapter_id':a,'relation_id':rel,'counterexamples':str(n)} for (a,rel),n in sorted(c.items())]
