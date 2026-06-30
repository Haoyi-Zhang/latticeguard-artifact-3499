import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.formal_core import deny_overrides_decision, deny_aware_monotonicity_holds, enumerate_core_policy_count
from scripts.run_full_evaluation import OpaRegoCliAdapter, Req, role_closure
rules=[{'effect':'allow','role':'viewer','action':'read','resource':'repo:public'},{'effect':'deny','role':'suspended','action':'read','resource':'repo:public'}]
assert deny_overrides_decision({'viewer'},rules,'read','repo:public')=='ALLOW'
assert deny_overrides_decision({'viewer','suspended'},rules,'read','repo:public')=='DENY'
assert not deny_aware_monotonicity_holds({'viewer'},{'viewer','suspended'},rules,'read','repo:public')
assert enumerate_core_policy_count() > 0

policy={
    'roles': {
        'leaf': {'inherits': ['mid_a','mid_b']},
        'mid_a': {'inherits': ['root']},
        'mid_b': {'inherits': ['root','audit']},
        'root': {'inherits': []},
        'audit': {'inherits': []},
        'cycle_a': {'inherits': ['cycle_b']},
        'cycle_b': {'inherits': ['cycle_a']},
    },
    'user_roles': {
        'alice': ['leaf'],
        'bob': ['cycle_a'],
    },
    'rules': [
        {'id':'r1','effect':'allow','role':'root','action':'read','resource':'repo:public'},
    ],
}
assert role_closure(policy,'alice') == {'leaf','mid_a','mid_b','root','audit'}
assert role_closure(policy,'bob') == {'cycle_a','cycle_b'}
assert role_closure(policy,'unknown') == set()
adapter=OpaRegoCliAdapter.__new__(OpaRegoCliAdapter)
data=adapter._data(policy, Req('req_alice_read_public','alice','read','repo:public'))
assert data['reachable_roles']['alice'] == ['audit','leaf','mid_a','mid_b','root']
assert data['reachable_roles']['bob'] == ['cycle_a','cycle_b']
print('formal_core PASS')
