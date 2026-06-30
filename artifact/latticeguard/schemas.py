from __future__ import annotations

import csv, json
from pathlib import Path
from typing import Iterable

SCHEMA_CONTRACTS = {
    "obligations.csv": {"required": {"row_id","adapter_id","source_id","relation_id","candidate_id","applicability_status","expected_invariant","before_decision","after_decision","oracle_status"}},
    "predicate_evaluations.csv": {"required": {"candidate_id","relation_id","computed_status","predicate_id","computed_reason","witness_hash"}},
    "soundness_checks.csv": {"required": {"candidate_id","relation_id","reference_oracle_status","soundness_check"}},
    "source_manifest.csv": {"required": {"source_id","kind","adapter_id","license","source_url","local_path","sha256"}},
    "counterexamples.json": {"json_required": {"failure_id","adapter_id","relation_id","source_id"}},
}


def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def validate_csv_schema(path: Path, required: set[str]) -> list[str]:
    if not path.exists():
        return [f"missing file: {path}"]
    with path.open('r', encoding='utf-8', newline='') as f:
        r=csv.DictReader(f); fields=set(r.fieldnames or [])
    missing=sorted(required-fields)
    return [f"{path.name} missing column {m}" for m in missing]


def validate_json_records(path: Path, required: set[str]) -> list[str]:
    if not path.exists():
        return [f"missing file: {path}"]
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, list):
        return [f"{path.name} is not a JSON list"]
    errors=[]
    for i,row in enumerate(data[:20]):
        missing=required-set(row)
        for m in missing:
            errors.append(f"{path.name}[{i}] missing key {m}")
    return errors


def validate_repository_schemas(root: Path) -> list[str]:
    errors=[]
    results=root/'results'
    for name,spec in SCHEMA_CONTRACTS.items():
        if 'required' in spec:
            p = (root/name) if name == 'source_manifest.csv' else (results/name)
            errors.extend(validate_csv_schema(p, set(spec['required'])))
        if 'json_required' in spec:
            errors.extend(validate_json_records(results/name, set(spec['json_required'])))
    return errors


def assert_no_hidden_denominator(rows: Iterable[dict[str,str]]) -> list[str]:
    errors=[]
    for r in rows:
        status=r.get('applicability_status','')
        oracle=r.get('oracle_status','')
        if status != 'APPLICABLE_EVALUATED' and oracle == 'PASS':
            errors.append(f"non-applicable row counted as pass: {r.get('row_id')}")
    return errors
