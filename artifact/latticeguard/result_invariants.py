from __future__ import annotations
import csv
from pathlib import Path

def check_result_invariants(root: Path) -> dict[str,list[str]]:
    errors={'denominator':[],'predicate_soundness':[],'coverage':[],'baseline':[]}
    with (root/'results'/'obligations.csv').open('r',encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            if r.get('applicability_status')!='APPLICABLE_EVALUATED' and r.get('oracle_status')=='PASS': errors['denominator'].append(r['row_id'])
    with (root/'results'/'soundness_checks.csv').open('r',encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            if r.get('soundness_check')!='PASS' or (r.get('applicability_status')=='APPLICABLE_EVALUATED' and r.get('reference_oracle_status')!='PASS'): errors['predicate_soundness'].append(r.get('candidate_id','?'))
    return errors
