#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.evidence_challenge_check import write_evidence_challenge_check, AUDIT_DIMENSIONS

def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def main() -> None:
    report = write_evidence_challenge_check(ROOT)
    errors=[]
    findings = read_csv(ROOT/'results'/'evidence_challenge_findings.csv')
    repairs = read_csv(ROOT/'results'/'evidence_challenge_repair_matrix.csv')
    impact = read_csv(ROOT/'results'/'paper_impact_matrix.csv')
    if len(findings) < 5: errors.append('fewer than five quality lenses')
    if any(r.get('blocking_after_repair') != 'false' for r in findings): errors.append('audit blocker remains after repair')
    dims = {r.get('dimension','') for r in repairs}
    missing = sorted(set(AUDIT_DIMENSIONS)-dims)
    if missing: errors.append('missing evidence-challenge dimensions: '+','.join(missing))
    if any(not str(r.get('repair_status','')).startswith('closed') for r in repairs): errors.append('unclosed repair rows present')
    if len(impact) < 4: errors.append('impact matrix too small')
    if report.get('status') != 'PASS': errors.append('evidence challenge gate status not PASS')
    out={'status':'PASS' if not errors else 'FAIL','errors':errors,'evidence_challenge_scorecard':report}
    print(json.dumps(out, indent=2, sort_keys=True))
    if errors: raise SystemExit(1)
if __name__=='__main__': main()
