from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.semantic_counterexample_replay import invariant_holds, mutant_decision, replay_rows


def _policy():
    return {
        'roles': {'viewer': {'inherits': []}, 'suspended': {'inherits': []}},
        'user_roles': {'alice': ['viewer', 'suspended']},
        'rules': [
            {'id': 'a', 'effect': 'allow', 'role': 'viewer', 'action': 'read', 'resource': 'repo:public'},
            {'id': 'd', 'effect': 'deny', 'role': 'suspended', 'action': 'read', 'resource': 'repo:public'},
        ]
    }


def test_seeded_mutant_semantics_are_independent():
    req = {'principal': 'alice', 'action': 'read', 'resource': 'repo:public'}
    assert mutant_decision('casbin_py_mutant_allow_overrides', _policy(), req) == 'ALLOW'
    assert mutant_decision('casbin_py_mutant_strip_denies', _policy(), req) == 'ALLOW'
    assert mutant_decision('cedar_py_mutant_ignore_forbid', _policy(), req) == 'ALLOW'
    assert mutant_decision('casbin_py_mutant_strip_allows', _policy(), req) == 'DENY'


def test_invariant_checker():
    assert invariant_holds('before==after', 'DENY', 'DENY')
    assert not invariant_holds('before==after', 'ALLOW', 'DENY')
    assert invariant_holds('before==ALLOW implies after==ALLOW', 'DENY', 'DENY')
    assert not invariant_holds('before==ALLOW implies after==ALLOW', 'ALLOW', 'DENY')


def test_full_counterexample_replay_if_results_exist():
    if not (ROOT / 'results' / 'counterexamples.json').exists():
        return
    rows = replay_rows(ROOT)
    assert rows
    assert all(r.status == 'PASS' for r in rows)
