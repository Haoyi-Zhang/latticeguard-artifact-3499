#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.evidence_queries import summarize_evidence
from latticeguard.repo_quality import count_python_lines, hygiene_scan
from latticeguard.scorecard import compute_score

def main() -> None:
    blockers=[]; evidence=summarize_evidence(ROOT); metrics=count_python_lines(ROOT); hygiene=hygiene_scan(ROOT.parent)
    if evidence['evaluated_obligations'] < 400: blockers.append('obligation depth below repository target')
    if evidence['native_benchmark_sources'] < 10: blockers.append('native benchmark source count below target')
    if evidence['model_check_cases'] < 70000 or evidence['model_check_failures'] != 0: blockers.append('bounded model checking target not met')
    if evidence['native_selftests'] < 30 or evidence['native_selftest_failures'] != 0: blockers.append('native selftest target not met')
    if metrics['python_lines'] < 4904: blockers.append('authored Python line target not met')
    blockers.extend(hygiene)
    score=compute_score(blockers); score.update({'blockers':blockers,'evidence_summary':evidence,'repository_metrics':metrics})
    print(json.dumps(score, indent=2, sort_keys=True))
    if blockers: raise SystemExit(1)
if __name__=='__main__': main()
