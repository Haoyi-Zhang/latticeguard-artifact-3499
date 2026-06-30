from __future__ import annotations
from copy import deepcopy
from typing import Any


def remove_hierarchy(policy: dict[str,Any]) -> dict[str,Any]:
    p=deepcopy(policy); p['inherits']={k:[] for k in p.get('inherits',{})}; return p

def strip_denies(policy: dict[str,Any]) -> dict[str,Any]:
    p=deepcopy(policy); p['rules']=[r for r in p.get('rules',[]) if r.get('effect')!='deny']; return p

def allow_overrides(policy: dict[str,Any]) -> dict[str,Any]:
    p=deepcopy(policy); p['combining']='allow_overrides_mutant'; return p

def ignore_forbid(policy: dict[str,Any]) -> dict[str,Any]:
    return strip_denies(policy)

def duplicate_rules(policy: dict[str,Any]) -> dict[str,Any]:
    p=deepcopy(policy); p['rules']=p.get('rules',[])+deepcopy(p.get('rules',[])); return p

def rename_action(policy: dict[str,Any], before:str, after:str) -> dict[str,Any]:
    p=deepcopy(policy)
    for r in p.get('rules',[]):
        if r.get('action')==before: r['action']=after
    return p

def inject_irrelevant_role(policy: dict[str,Any]) -> dict[str,Any]:
    p=deepcopy(policy); p.setdefault('roles',[]).append('irrelevant_role'); p.setdefault('assignments',{})['ghost']=['irrelevant_role']; return p

def mutation_catalog() -> list[dict[str,str]]:
    return [
        {'mutant_id':'allow_overrides','fault_model':'combining algorithm drift','target_relation':'DO'},
        {'mutant_id':'strip_denies','fault_model':'deny rules ignored','target_relation':'DO/SR'},
        {'mutant_id':'no_hierarchy','fault_model':'role inheritance ignored','target_relation':'PA/HC/HR'},
        {'mutant_id':'ignore_forbid','fault_model':'Cedar forbid rules ignored','target_relation':'DO/SR'},
        {'mutant_id':'duplicate_rules','fault_model':'idempotence stress','target_relation':'ID'},
        {'mutant_id':'irrelevant_extension','fault_model':'unreachable material stress','target_relation':'IE'},
    ]
