#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.reference_integrity_gate import write_reference_integrity_gate


def main() -> None:
    summary = write_reference_integrity_gate(ROOT)
    errors = []
    if summary.get('status') != 'PASS':
        errors.append('reference integrity gate status is not PASS')
    if int(summary.get('reference_entries', 0)) < 70:
        errors.append('reference count below intended ICSE range')
    if int(summary.get('reference_entries', 0)) > 80:
        errors.append('reference count above intended ICSE range')
    if summary.get('reference_entries') != summary.get('cited_entries'):
        errors.append('some bibliography entries are not cited')
    if summary.get('reference_entries') != summary.get('crosswalk_rows_covered'):
        errors.append('some bibliography entries lack crosswalk rows')
    report = {'status': 'PASS' if not errors else 'FAIL', 'errors': errors, **summary}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
