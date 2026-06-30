#!/usr/bin/env python3
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.mechanized_law_kernel import RELATIONS, write_mechanized_law_kernel


def main() -> None:
    report = write_mechanized_law_kernel(ROOT)
    rows = list(csv.DictReader((ROOT / 'results' / 'mechanized_law_kernel.csv').open(newline='', encoding='utf-8')))
    errors = []
    if report.get('status') != 'PASS':
        errors.append('mechanized law kernel report is not PASS')
    if int(report.get('relations_covered', 0)) != len(RELATIONS):
        errors.append('not all relation families covered')
    if int(report.get('failures', 1)) != 0:
        errors.append('mechanized law kernel contains failures')
    if len(rows) < 400:
        errors.append('mechanized law kernel case count below threshold')
    counts = {rid: 0 for rid in RELATIONS}
    for row in rows:
        counts[row['relation_id']] = counts.get(row['relation_id'], 0) + 1
        if row['status'] != 'PASS':
            errors.append('non-PASS row: ' + row['case_id'])
    if any(v < 30 for v in counts.values()):
        errors.append('some relation has too few mechanized proof cases: ' + repr(counts))
    out = {'status': 'PASS' if not errors else 'FAIL', 'errors': errors, **report}
    print(json.dumps(out, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
