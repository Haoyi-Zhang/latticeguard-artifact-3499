#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.adapter_reference_agreement import write_adapter_reference_agreement


def main() -> None:
    summary = write_adapter_reference_agreement(ROOT)
    errors = []
    if summary.get('status') != 'PASS':
        errors.append('adapter-reference agreement status is not PASS')
    if int(summary.get('rows_checked', 0)) != 15840:
        errors.append('adapter-reference agreement rows do not match the three-adapter primary obligation count')
    if int(summary.get('adapters_covered', 0)) != 3:
        errors.append('adapter-reference agreement must cover casbin_py, cedar_py, and hash-gated opa_rego_cli')
    if int(summary.get('relations_covered', 0)) != 12:
        errors.append('adapter-reference agreement does not cover all 12 relations')
    report = {'status': 'PASS' if not errors else 'FAIL', 'errors': errors, **summary}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
