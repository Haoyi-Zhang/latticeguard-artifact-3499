#!/usr/bin/env python3
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.oracle_efficacy import write_oracle_efficacy


def main() -> None:
    report = write_oracle_efficacy(ROOT)
    rows = list(csv.DictReader((ROOT / 'results' / 'oracle_efficacy_summary.csv').open(newline='', encoding='utf-8')))
    errors = []
    if report.get('status') != 'PASS':
        errors.append('oracle efficacy summary status is not PASS')
    if int(report.get('full_oracle_seeded_killed', 0)) <= 0:
        errors.append('full oracle killed no seeded drifts')
    if int(report.get('semantic_counterexamples_replayed', 0)) != int(report.get('full_oracle_seeded_killed', -1)):
        errors.append('semantic replay count does not match killed seeded drifts')
    if not any(r['baseline_id'] == 'NO_APPLICABILITY_GATE' and int(r['invalid_transformations_admitted'] or 0) > 0 for r in rows):
        errors.append('no-gate baseline does not expose invalid transformations')
    if not any(r['baseline_id'] == 'LATTICEGUARD_FULL_ORACLE' and r['denominator_safety_score'] == '1.000000' for r in rows):
        errors.append('full oracle denominator safety score missing')
    out = {'status': 'PASS' if not errors else 'FAIL', 'errors': errors, **report, 'rows': len(rows)}
    print(json.dumps(out, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
