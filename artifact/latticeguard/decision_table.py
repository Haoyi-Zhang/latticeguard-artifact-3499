from __future__ import annotations
from typing import Iterable

def summarize_decisions(rows: Iterable[dict[str,str]]) -> dict[str,int]:
    counts={'ALLOW_before':0,'DENY_before':0,'ALLOW_after':0,'DENY_after':0,'PASS':0,'FAIL':0}
    for r in rows:
        b=r.get('before_decision',''); a=r.get('after_decision',''); o=r.get('oracle_status','')
        if b=='ALLOW': counts['ALLOW_before']+=1
        if b=='DENY': counts['DENY_before']+=1
        if a=='ALLOW': counts['ALLOW_after']+=1
        if a=='DENY': counts['DENY_after']+=1
        if o=='PASS': counts['PASS']+=1
        if o=='FAIL': counts['FAIL']+=1
    return counts

def denominator_partition(rows: Iterable[dict[str,str]]) -> dict[str,int]:
    out={}
    for r in rows:
        st=r.get('applicability_status','')
        out[st]=out.get(st,0)+1
    return out
