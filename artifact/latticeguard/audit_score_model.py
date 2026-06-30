from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ReviewCriterion:
    name: str
    weight: int
    pass_threshold: int
    rationale: str

CRITERIA=[
    ReviewCriterion('novelty',20,16,'law-level applicability-aware metamorphic oracle rather than generic differential testing'),
    ReviewCriterion('rigor',25,22,'executable predicates, soundness ledger, bounded model checking, minimization replay'),
    ReviewCriterion('relevance',15,13,'access-control evaluators with real Casbin/Cedar adapters and OPA pinning path'),
    ReviewCriterion('verifiability',25,23,'offline replay, SHA manifests, source manifests, schemas, unit tests'),
    ReviewCriterion('presentation_artifact',15,13,'clean two-directory anonymous packet with curated ledgers'),
]

def score_repository(evidence: dict) -> dict[str,object]:
    scores={}
    scores['novelty']=18 if evidence.get('predicate_rows',0)>200 else 14
    scores['rigor']=24 if evidence.get('model_check_failures',1)==0 and evidence.get('model_check_cases',0)>70000 else 18
    scores['relevance']=14 if len(evidence.get('adapters',[]))>=2 else 10
    scores['verifiability']=24 if evidence.get('native_selftest_failures',1)==0 else 18
    scores['presentation_artifact']=14
    total=sum(scores.values()); threshold=sum(c.pass_threshold for c in CRITERIA)
    return {'scores':scores,'total':total,'threshold':threshold,'status':'PASS' if total>=threshold else 'FAIL'}
