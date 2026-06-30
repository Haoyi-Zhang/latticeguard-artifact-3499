from __future__ import annotations
ADAPTER_CONTRACTS = {
    'casbin_py': {'kind':'real_local_adapter','decisions': {'ALLOW','DENY'}, 'unsupported': set(), 'semantics':['deny-overrides fragment','role hierarchy']},
    'cedar_py': {'kind':'real_local_adapter','decisions': {'ALLOW','DENY'}, 'unsupported': set(), 'semantics':['forbid-overrides-permit','default deny','PARC requests']},
    'opa_rego_cli': {'kind':'pinned_optional_target','decisions': {'ALLOW','DENY'}, 'unsupported': {'missing_vetted_executable'}, 'semantics':['Rego allow/deny harness']},
}

def validate_adapter_contracts() -> list[str]:
    errors=[]
    for aid,c in ADAPTER_CONTRACTS.items():
        if not c['decisions'] >= {'ALLOW','DENY'}: errors.append(f'{aid} missing binary decisions')
        if not c['semantics']: errors.append(f'{aid} missing semantic notes')
    return errors
