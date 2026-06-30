import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.artifact_integrity_check import package_gate
report=package_gate(ROOT)
assert report['status']=='PASS', report
print('artifact_integrity_check PASS')
