#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.upstream_benchmarks import upstream_rows, as_csv_rows

def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader(); w.writerows(rows)

def main():
    audits=upstream_rows(ROOT/'source_manifest.csv', ROOT/'results'/'native_selftest_results.csv')
    rows=as_csv_rows(audits)
    write_csv(ROOT/'results'/'upstream_benchmark_audit.csv', rows, ['source_id','family','fixture_count','selftest_count','selftest_failures','source_urls','raw_hash','verdict'])
    failures=[r for r in rows if r['verdict']!='PASS']
    upstream=[r for r in rows if r['source_id'].startswith('public_upstream_')]
    report={
        'status': 'PASS' if not failures and len(upstream) >= 7 else 'FAIL',
        'native_benchmark_sources': len(rows),
        'upstream_native_sources': len(upstream),
        'failures': failures,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if report['status']!='PASS':
        raise SystemExit(1)
if __name__=='__main__': main()
