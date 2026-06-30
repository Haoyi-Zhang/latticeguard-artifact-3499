#!/usr/bin/env python3
from __future__ import annotations
import ast, csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/'latticeguard'
SCRIPTS=ROOT/'scripts'
TESTS=ROOT/'tests'

def count_lines(paths):
    total=0; files=0
    for p in paths:
        if p.name.startswith('__'):
            continue
        files+=1; total+=len(p.read_text(encoding='utf-8', errors='ignore').splitlines())
    return files,total

def public_functions(path: Path) -> int:
    tree=ast.parse(path.read_text(encoding='utf-8'))
    return sum(1 for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith('_'))

def main():
    pkg_files=list(PKG.glob('*.py'))
    script_files=list(SCRIPTS.glob('*.py'))
    test_files=list(TESTS.glob('*.py'))
    pkg_count,pkg_lines=count_lines(pkg_files)
    script_count,script_lines=count_lines(script_files)
    test_count,test_lines=count_lines(test_files)
    api=sum(public_functions(p) for p in pkg_files)
    issues=[]
    if pkg_count < 40: issues.append('library module count below 40')
    if pkg_lines < 2600: issues.append('library authored lines below 2600')
    if script_count < 30: issues.append('verifier/runner script count below 30')
    if test_lines < 250: issues.append('unit/invariant test lines below 250')
    if api < 90: issues.append('public package API surface below 90 functions/classes')
    summary_path=ROOT/'results'/'summary.json'
    if summary_path.exists():
        summary=json.loads(summary_path.read_text(encoding='utf-8'))
        if int(summary.get('primary_evaluated_obligations',0)) < 576: issues.append('obligation count below locked protocol threshold')
        if int(summary.get('native_selftest_failures',1)) != 0: issues.append('native selftest failures present')
    report={'status':'PASS' if not issues else 'FAIL','issues':issues,'package_modules':pkg_count,'package_lines':pkg_lines,'script_files':script_count,'script_lines':script_lines,'test_files':test_count,'test_lines':test_lines,'public_api_items':api}
    (ROOT/'results'/'repository_depth.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2, sort_keys=True))
    if issues: raise SystemExit(1)
if __name__=='__main__': main()
