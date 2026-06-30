from __future__ import annotations
WEIGHTS={'replay':20,'benchmark':15,'theory':15,'coverage':15,'schema':12,'counterexamples':10,'hygiene':8,'audit_lenses':5}
def compute_score(blockers:list[str]) -> dict[str,object]:
    score=0 if blockers else sum(WEIGHTS.values())
    return {'score':score,'grade':'A' if score>=90 else 'B' if score>=80 else 'C','status':'PASS' if not blockers else 'FAIL','weights':WEIGHTS,'points':WEIGHTS if not blockers else {k:0 for k in WEIGHTS}}
