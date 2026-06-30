import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.schemas import assert_no_hidden_denominator
assert assert_no_hidden_denominator([{'row_id':'x','applicability_status':'REJECTED_NOT_COUNTED','oracle_status':'REJECTED_NOT_COUNTED'}]) == []
assert assert_no_hidden_denominator([{'row_id':'x','applicability_status':'REJECTED_NOT_COUNTED','oracle_status':'PASS'}])
print('result_invariants PASS')
