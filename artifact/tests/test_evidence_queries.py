import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.oracle_catalog import relation_ids
assert len(relation_ids())==12
print('evidence_queries PASS')
