from __future__ import annotations
import csv, hashlib, json
from collections import Counter
from pathlib import Path


def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def read_csv_if_exists(path: Path):
    return read_csv(path) if path.exists() else []


def digest(obj) -> str:
    blob=json.dumps(obj, sort_keys=True, separators=(',',':'))
    return hashlib.sha256(blob.encode()).hexdigest()


def build_certificate(root: Path) -> dict:
    res=root/'results'
    sound=read_csv(res/'soundness_checks.csv')
    model=json.loads((res/'model_check_summary.json').read_text(encoding='utf-8'))
    contracts=read_csv(res/'relation_contracts.csv')
    theorem_rows=read_csv_if_exists(res/'theorem_ledger.csv')
    theorem_obligations=read_csv_if_exists(res/'theorem_obligations.csv')
    mechanized_kernel=json.loads((res/'mechanized_law_kernel.json').read_text(encoding='utf-8')) if (res/'mechanized_law_kernel.json').exists() else {}
    failures=[r for r in sound if r.get('soundness_check')!='PASS']
    theorem_failures=[r for r in theorem_rows if r.get('status')!='PASS']
    obligation_failures=[r for r in theorem_obligations if r.get('status')!='PASS']
    sound_by_relation=Counter(r.get('relation_id','') for r in sound)
    contract_ids=sorted(r.get('relation_id','') for r in contracts)
    theorem_ids=sorted(r.get('relation_id','') for r in theorem_rows)
    certificate_body={
        'relation_contracts': contracts,
        'soundness_rows': sound,
        'model_summary': model,
        'theorem_ledger': theorem_rows,
        'theorem_obligations': theorem_obligations,
        'mechanized_law_kernel': mechanized_kernel,
    }
    status = (
        len(contracts)==12 and not failures and int(model.get('failures',0))==0
        and len(theorem_rows)==12 and len(theorem_obligations)==48
        and not theorem_failures and not obligation_failures
        and mechanized_kernel.get('status')=='PASS' and int(mechanized_kernel.get('failures',1))==0
    )
    return {
        'certificate_kind':'latticeguard_relation_soundness_certificate',
        'relation_contracts':len(contracts),
        'contract_relation_ids':contract_ids,
        'theorem_rows':len(theorem_rows),
        'theorem_relation_ids':theorem_ids,
        'proof_obligations':len(theorem_obligations),
        'theorem_failures':len(theorem_failures),
        'proof_obligation_failures':len(obligation_failures),
        'soundness_rows':len(sound),
        'soundness_rows_by_relation':dict(sorted(sound_by_relation.items())),
        'soundness_failures':len(failures),
        'bounded_model_cases':model.get('cases_checked',0),
        'bounded_model_failures':model.get('failures',0),
        'bounded_model_relations':model.get('relations_covered',0),
        'mechanized_kernel_cases':mechanized_kernel.get('cases_checked',0),
        'mechanized_kernel_failures':mechanized_kernel.get('failures',0),
        'mechanized_kernel_relations':mechanized_kernel.get('relations_covered',0),
        'bounded_model_cases_by_relation':model.get('relation_counts',{}),
        'digest_scope':'all_relation_contracts_all_soundness_rows_model_summary_theorem_ledger_theorem_obligations_mechanized_law_kernel',
        'digest': digest(certificate_body),
        'status':'PASS' if status else 'FAIL'
    }
