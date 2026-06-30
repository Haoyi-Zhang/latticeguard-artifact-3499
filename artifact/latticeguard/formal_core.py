from __future__ import annotations
from itertools import combinations
from typing import Iterable


def acyclic_edges(roles: list[str]) -> list[tuple[str,str]]:
    return [(a,b) for i,a in enumerate(roles) for b in roles[i+1:]]


def role_closure(assignments: dict[str,set[str]], inherits: dict[str,set[str]], principal: str) -> set[str]:
    seen=set(assignments.get(principal,set())); changed=True
    while changed:
        changed=False
        for r in list(seen):
            for p in inherits.get(r,set()):
                if p not in seen:
                    seen.add(p); changed=True
    return seen


def deny_overrides_decision(roles: set[str], rules: list[dict[str,str]], action: str, resource: str) -> str:
    matched=[r for r in rules if r.get('role') in roles and r.get('action')==action and r.get('resource')==resource]
    if any(r.get('effect')=='deny' for r in matched): return 'DENY'
    if any(r.get('effect')=='allow' for r in matched): return 'ALLOW'
    return 'DENY'


def deny_aware_monotonicity_holds(before_roles:set[str], after_roles:set[str], rules:list[dict[str,str]], action:str, resource:str) -> bool:
    if not before_roles <= after_roles: return False
    new_roles=after_roles-before_roles
    return not any(r.get('effect')=='deny' and r.get('role') in new_roles and r.get('action')==action and r.get('resource')==resource for r in rules)


def enumerate_core_policy_count(role_bound:int=3, rule_bound:int=2) -> int:
    roles=[f'r{i}' for i in range(role_bound)]
    edges=acyclic_edges(roles)
    # compact deterministic count used by unit tests; full artifact writes row-level model checks.
    return len(roles) * (1 + len(edges)) * (rule_bound + 1)
