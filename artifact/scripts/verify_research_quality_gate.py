#!/usr/bin/env python3
from __future__ import annotations
import sys

sys.dont_write_bytecode = True

import csv
import json
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.runtime_hygiene import python_bytecode_env
from latticeguard.research_quality_gate import write_quality_gate

PREREQUISITES = [
    'verify_research_quality.py',
    'verify_mechanized_law_kernel.py',
    'verify_oracle_efficacy.py',
    'verify_repository_depth.py',
    'verify_artifact_depth.py',
    'verify_evidence_challenge_check.py',
    'verify_proof_certificate.py',
    'verify_adapter_reference_agreement.py',
    'verify_reference_integrity_gate.py',
    'verify_source_provenance_gate.py',
    'verify_content_residue_gate.py',
    'verify_denominator_integrity_gate.py',
    'verify_module_import_gate.py',
    'verify_dependency_provenance_gate.py',
]

def ensure_prerequisites() -> None:
    env = python_bytecode_env()
    for script in PREREQUISITES:
        subprocess.run([sys.executable, '-B', str(ROOT / 'scripts' / script)], check=True, stdout=subprocess.DEVNULL, env=env)


def main() -> None:
    ensure_prerequisites()
    # Preliminary gate gives claim_traceability a concrete quality-gate evidence file.
    write_quality_gate(ROOT)
    subprocess.run([sys.executable, '-B', str(ROOT / 'scripts' / 'verify_claim_traceability.py')], check=True, stdout=subprocess.DEVNULL, env=python_bytecode_env())
    report = write_quality_gate(ROOT)
    rows = list(csv.DictReader((ROOT / 'results' / 'research_quality_gate_matrix.csv').open(newline='', encoding='utf-8')))
    errors = []
    if report.get('status') != 'PASS':
        errors.append('research-quality gate analysis has open gaps')
    if len(rows) < 14:
        errors.append('too few research-quality lenses')
    for row in rows:
        if row['status'] != 'closed':
            errors.append('unclosed lens ' + row['quality_lens'])
        for rel in row['evidence_file'].split(';'):
            rel = rel.strip()
            if rel and not (ROOT.parent / rel).exists():
                errors.append(f'missing evidence {rel}')
    out = {'status': 'PASS' if not errors else 'FAIL', 'errors': errors, **report}
    print(json.dumps(out, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
