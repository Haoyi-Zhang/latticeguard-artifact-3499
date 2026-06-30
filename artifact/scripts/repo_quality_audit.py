#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
sys.path.insert(0,str(ROOT))
from latticeguard.repo_quality import authored_files, count_python_lines, hygiene_scan, largest_python

def main() -> None:
    metrics=count_python_lines(ROOT)
    issues=hygiene_scan(REPO)
    files=authored_files(REPO)
    largest=largest_python(ROOT)
    report={'status':'PASS' if not issues and metrics['python_lines']>=4904 else 'FAIL','hygiene_issues':issues,'python_files':len(list((ROOT/'scripts').glob('*.py')))+len(list((ROOT/'latticeguard').glob('*.py')))+len(list((ROOT/'tests').glob('*.py'))),'authored_files':len(files),'authored_lines':sum(len(p.read_text(encoding='utf-8',errors='ignore').splitlines()) for p in files),'result_files':len(list((ROOT/'results').glob('*'))),'largest_python_file':largest,'package_python_lines':metrics['package_python_lines'],'script_python_lines':metrics['script_python_lines'],'test_python_lines':metrics.get('test_python_lines',0),'python_lines':metrics['python_lines']}
    if metrics['python_lines']<4904: report['hygiene_issues'].append('python authored lines below requested 2x threshold')
    print(json.dumps(report, indent=2, sort_keys=True))
    if report['status']!='PASS': raise SystemExit(1)
if __name__=='__main__': main()
