from __future__ import annotations
RELATION_CATALOG = [
 ('DD','Default deny','no reachable allow or deny','before=DENY and after=DENY'),
 ('DO','Deny dominance','matching allow plus added matching deny','before=ALLOW and after=DENY'),
 ('PA','Deny-aware principal monotonicity','role closure superset and no newly matching deny','ALLOW preserved'),
 ('DA','Deny antitonicity','deny witness remains reachable','DENY preserved'),
 ('IE','Irrelevant extension','new material outside request-reachable slice','decision unchanged'),
 ('ID','Idempotence','duplicate semantic rule','decision unchanged'),
 ('HC','Hierarchy closure','added edge already implied by transitive closure','decision unchanged'),
 ('HR','Hierarchy refactoring','child role inherits original role and assignment is rewritten consistently','decision unchanged'),
 ('SR','Shadowed rule removal','removed allow is shadowed by matching deny','DENY preserved'),
 ('RO','Rule-order invariance','same unordered rule multiset and no priority/first/last-match fragment','decision unchanged'),
 ('AR','Alpha renaming','injective renaming outside requested principal/resource/action slice','decision unchanged'),
 ('SM','Scope split/merge','disjoint scope rewrite preserves target permission','decision unchanged'),
]

def relation_ids() -> list[str]: return [r[0] for r in RELATION_CATALOG]
def relation_table() -> list[dict[str,str]]: return [{'relation_id':a,'name':b,'predicate_summary':c,'invariant_summary':d} for a,b,c,d in RELATION_CATALOG]
def validate_relation_catalog() -> list[str]:
    ids=relation_ids(); errors=[]
    if len(ids)!=12: errors.append('expected 12 relations')
    if len(set(ids))!=len(ids): errors.append('duplicate relation ids')
    for row in relation_table():
        if not row['predicate_summary'] or not row['invariant_summary']: errors.append('empty relation summary '+row['relation_id'])
    return errors
