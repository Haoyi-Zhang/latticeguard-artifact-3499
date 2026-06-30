from __future__ import annotations
from pathlib import Path
REQUIRED=['README.md','reproduction.md','requirements.txt','source_manifest.csv','evidence/SHA256SUMS.csv','scripts/run_full_evaluation.py','scripts/verify_full_claims.py']
def check_reproducibility_contract(root: Path) -> list[str]: return [f'missing {p}' for p in REQUIRED if not (root/p).exists()]
