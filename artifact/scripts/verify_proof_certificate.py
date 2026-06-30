#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.proof_certificate import build_certificate
from latticeguard.theorem_ledger import write_theorem_ledgers
from latticeguard.mechanized_law_kernel import write_mechanized_law_kernel

if not (ROOT/'results'/'theorem_ledger.csv').exists() or not (ROOT/'results'/'theorem_obligations.csv').exists():
    write_theorem_ledgers(ROOT)
if not (ROOT/'results'/'mechanized_law_kernel.json').exists() or not (ROOT/'results'/'mechanized_law_kernel.csv').exists():
    write_mechanized_law_kernel(ROOT)
out=build_certificate(ROOT)
(ROOT/'results'/'proof_certificate.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
print(json.dumps(out, indent=2, sort_keys=True))
if out['status']!='PASS': raise SystemExit(1)
