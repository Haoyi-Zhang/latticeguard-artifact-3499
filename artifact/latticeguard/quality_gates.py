from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class QualityGate:
    gate_id: str
    description: str
    metric: str
    threshold: float
    comparator: str
    severity: str

QUALITY_GATES = [
    QualityGate('QG_REPLAY_001','claim verifier passes','verify_full_claims',1,'==','P0'),
    QualityGate('QG_REPLAY_002','predicate verifier passes','verify_predicate_witnesses',1,'==','P0'),
    QualityGate('QG_REPLAY_003','minimization replay passes','verify_minimization_replay',1,'==','P0'),
    QualityGate('QG_SCHEMA_001','schema contract passes','verify_schema_contracts',1,'==','P0'),
    QualityGate('QG_SCHEMA_002','manifest integrity passes','verify_manifest_integrity',1,'==','P0'),
    QualityGate('QG_BENCH_001','benchmark source count','benchmark_sources',17,'>=','P1'),
    QualityGate('QG_BENCH_002','native fixture file count','native_files',20,'>=','P1'),
    QualityGate('QG_THEORY_001','bounded model check cases','model_check_cases',70000,'>=','P1'),
    QualityGate('QG_THEORY_002','bounded model check failures','model_check_failures',0,'==','P0'),
    QualityGate('QG_CODE_001','authored Python lines','python_lines',4904,'>=','P1'),
    QualityGate('QG_CODE_002','hygiene issues','hygiene_issues',0,'==','P0'),
    QualityGate('QG_CEX_001','counterexample count','counterexamples',170,'>=','P1'),
]

def compare(value: float, threshold: float, comparator: str) -> bool:
    if comparator == '>=': return value >= threshold
    if comparator == '<=': return value <= threshold
    if comparator == '==': return value == threshold
    if comparator == '>': return value > threshold
    if comparator == '<': return value < threshold
    raise ValueError(comparator)

def evaluate_gates(metrics: dict[str,float]) -> list[dict[str,object]]:
    rows=[]
    for gate in QUALITY_GATES:
        value=metrics.get(gate.metric,0)
        passed=compare(value, gate.threshold, gate.comparator)
        rows.append({'gate_id':gate.gate_id,'metric':gate.metric,'value':value,'threshold':gate.threshold,'comparator':gate.comparator,'severity':gate.severity,'status':'PASS' if passed else 'FAIL','description':gate.description})
    return rows

def blocking_gates(rows:list[dict[str,object]]) -> list[dict[str,object]]:
    return [r for r in rows if r['status']!='PASS' and r['severity']=='P0']
