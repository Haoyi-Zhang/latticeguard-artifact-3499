from __future__ import annotations

LAW_FAMILIES={
    'deny_allow_combining':['DD','DO','SR'],
    'principal_relation':['PA','DA','SM'],
    'hierarchy_refactoring':['HC','HR'],
    'irrelevance_and_idempotence':['IE','ID'],
    'resource_action_relation':['RO','AR'],
}

def family_for_relation(relation_id: str) -> str:
    for fam,rels in LAW_FAMILIES.items():
        if relation_id in rels: return fam
    return 'unknown'

def ontology_rows() -> list[dict[str,str]]:
    rows=[]
    for fam,rels in LAW_FAMILIES.items():
        for rel in rels:
            rows.append({'law_family':fam,'relation_id':rel,'artifact_role':'metamorphic_obligation_family'})
    return rows

def ontology_errors() -> list[str]:
    rels=[r for rs in LAW_FAMILIES.values() for r in rs]
    errors=[]
    if len(rels)!=12: errors.append('ontology must contain 12 relations')
    if len(set(rels))!=len(rels): errors.append('duplicate ontology relation')
    return errors
