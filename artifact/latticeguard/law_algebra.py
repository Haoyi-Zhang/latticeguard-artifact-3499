from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, chain
from typing import Iterable, Iterator, Mapping

@dataclass(frozen=True)
class Rule:
    effect: str
    role: str
    action: str
    resource: str

@dataclass(frozen=True)
class Request:
    principal: str
    action: str
    resource: str

@dataclass(frozen=True)
class CorePolicy:
    assignments: Mapping[str, frozenset[str]]
    inherits: Mapping[str, frozenset[str]]
    rules: tuple[Rule, ...]


def powerset(items: Iterable[str], limit: int | None = None) -> Iterator[tuple[str, ...]]:
    xs=tuple(items)
    max_len=len(xs) if limit is None else min(limit, len(xs))
    for n in range(max_len+1):
        yield from combinations(xs,n)


def transitive_closure(seed: Iterable[str], edges: Mapping[str, Iterable[str]]) -> frozenset[str]:
    seen=set(seed); changed=True
    while changed:
        changed=False
        for x in list(seen):
            for y in edges.get(x,()):
                if y not in seen:
                    seen.add(y); changed=True
    return frozenset(seen)


def reachable_roles(policy: CorePolicy, principal: str) -> frozenset[str]:
    return transitive_closure(policy.assignments.get(principal, frozenset()), policy.inherits)


def matching_rules(policy: CorePolicy, request: Request) -> tuple[Rule, ...]:
    roles=reachable_roles(policy, request.principal)
    return tuple(r for r in policy.rules if r.role in roles and r.action == request.action and r.resource == request.resource)


def decide(policy: CorePolicy, request: Request) -> str:
    ms=matching_rules(policy, request)
    if any(r.effect == 'deny' for r in ms): return 'DENY'
    if any(r.effect == 'allow' for r in ms): return 'ALLOW'
    return 'DENY'


def relation_dd(policy: CorePolicy, request: Request) -> tuple[bool,str]:
    ms=matching_rules(policy, request)
    return (not ms, 'no reachable matching allow/deny' if not ms else 'matching rule exists')


def relation_do(before: CorePolicy, after: CorePolicy, request: Request) -> tuple[bool,str]:
    b=matching_rules(before, request); a=matching_rules(after, request)
    return (any(r.effect=='allow' for r in b) and any(r.effect=='deny' for r in a), 'matching allow before and matching deny after')


def relation_pa(before: CorePolicy, after: CorePolicy, before_req: Request, after_req: Request) -> tuple[bool,str]:
    br=reachable_roles(before, before_req.principal); ar=reachable_roles(after, after_req.principal)
    if not br <= ar: return (False, 'role closure is not a superset')
    new=ar-br
    deny=any(r.effect=='deny' and r.role in new and r.action==after_req.action and r.resource==after_req.resource for r in after.rules)
    return (not deny, 'deny-aware role superset without newly matching deny' if not deny else 'new matching deny breaks monotonicity')


def relation_ie(before: CorePolicy, after: CorePolicy, request: Request) -> tuple[bool,str]:
    br=reachable_roles(before, request.principal); ar=reachable_roles(after, request.principal)
    if br != ar: return (False, 'reachable role closure changed')
    before_ms={(r.effect,r.role,r.action,r.resource) for r in matching_rules(before, request)}
    after_ms={(r.effect,r.role,r.action,r.resource) for r in matching_rules(after, request)}
    return (before_ms == after_ms, 'matching slice unchanged' if before_ms==after_ms else 'matching slice changed')


def relation_id(before: CorePolicy, after: CorePolicy) -> tuple[bool,str]:
    b={(r.effect,r.role,r.action,r.resource) for r in before.rules}
    a=[(r.effect,r.role,r.action,r.resource) for r in after.rules]
    return (set(a) == b and len(a) >= len(b), 'duplicates only' if set(a)==b else 'semantic rule set changed')


def law_soundness_dispatch(relation_id: str, before: CorePolicy, after: CorePolicy, before_req: Request, after_req: Request) -> tuple[bool,str]:
    if relation_id == 'DD': return relation_dd(before, before_req)
    if relation_id == 'DO': return relation_do(before, after, before_req)
    if relation_id == 'PA': return relation_pa(before, after, before_req, after_req)
    if relation_id == 'IE': return relation_ie(before, after, before_req)
    if relation_id == 'ID': return relation_id(before, after)
    return (True, 'relation checked in primary artifact runner')


def policy_digest_material(policy: CorePolicy) -> tuple:
    return (
        tuple(sorted((k, tuple(sorted(v))) for k,v in policy.assignments.items())),
        tuple(sorted((k, tuple(sorted(v))) for k,v in policy.inherits.items())),
        tuple(sorted((r.effect,r.role,r.action,r.resource) for r in policy.rules)),
    )


def normalize_effect(effect: str) -> str:
    e=effect.strip().lower()
    if e in {'allow','permit'}: return 'allow'
    if e in {'deny','forbid'}: return 'deny'
    raise ValueError(f'unknown effect: {effect}')


def rule_from_mapping(row: Mapping[str,str]) -> Rule:
    return Rule(normalize_effect(row['effect']), row['role'], row['action'], row['resource'])


def request_from_mapping(row: Mapping[str,str]) -> Request:
    return Request(row['principal'], row['action'], row['resource'])


def finite_policy_samples() -> list[CorePolicy]:
    roles=['viewer','editor','suspended']
    users=['alice','mallory']
    policies=[]
    for user_roles in powerset(roles, limit=2):
        assignments={'alice': frozenset(user_roles), 'mallory': frozenset({'suspended'})}
        for parent in [(), ('viewer',)]:
            inherits={'editor': frozenset(parent), 'viewer': frozenset(), 'suspended': frozenset()}
            rules=(Rule('allow','viewer','read','repo:public'), Rule('deny','suspended','read','repo:public'))
            policies.append(CorePolicy(assignments, inherits, rules))
    return policies


def exhaustive_allow_preservation_checks() -> list[dict[str,str]]:
    rows=[]
    req=Request('alice','read','repo:public')
    for idx,before in enumerate(finite_policy_samples()):
        for jdx,after in enumerate(finite_policy_samples()):
            ok,reason=relation_pa(before, after, req, req)
            if ok:
                rows.append({'case_id':f'pa_{idx}_{jdx}','before_decision':decide(before,req),'after_decision':decide(after,req),'predicate_reason':reason,'sound':str(not (decide(before,req)=='ALLOW' and decide(after,req)!='ALLOW')).lower()})
    return rows
