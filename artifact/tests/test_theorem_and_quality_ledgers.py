from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.theorem_ledger import RELATION_THEOREMS
from latticeguard.research_quality import novelty_matrix_rows, research_question_rows

assert len(RELATION_THEOREMS) == 12
assert {row['relation_id'] for row in RELATION_THEOREMS} == {'DD','DO','PA','DA','IE','ID','HC','HR','SR','RO','AR','SM'}
for row in RELATION_THEOREMS:
    assert row['core_side_condition']
    assert row['missing_side_condition_counterexample']

if (ROOT / 'results' / 'summary.json').exists():
    assert len(research_question_rows(ROOT)) == 5
    assert len(novelty_matrix_rows(ROOT)) == 5
