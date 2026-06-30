#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from latticeguard.runtime_hygiene import cleanup_bytecode_artifacts, python_bytecode_env, scan_bytecode_artifacts
TESTS=sorted((ROOT/'tests').glob('test_*.py'))

TRANSIENT_DIR_NAMES = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
TRANSIENT_SUFFIXES = {'.pyc', '.pyo'}

def clean_release_residue() -> None:
    for path in sorted(ROOT.parent.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and path.name in TRANSIENT_DIR_NAMES:
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() and path.suffix in TRANSIENT_SUFFIXES:
            try:
                path.unlink()
            except FileNotFoundError:
                pass

def run_one(t: Path) -> dict[str, object]:
    try:
        env=python_bytecode_env(os.environ.copy())
        p=subprocess.run([sys.executable,'-B',str(t)], cwd=str(ROOT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return {'test':str(t.relative_to(ROOT)),'status':'PASS' if p.returncode==0 else 'FAIL','returncode':p.returncode,'stdout':p.stdout[-2000:] or ('PASS\n' if p.returncode==0 else ''),'stderr':p.stderr[-2000:]}
    except subprocess.TimeoutExpired as exc:
        return {'test':str(t.relative_to(ROOT)),'status':'TIMEOUT','returncode':124,'stdout':(exc.stdout or '')[-2000:] if isinstance(exc.stdout,str) else '', 'stderr':'timeout'}

def main() -> None:
    rows=[run_one(t) for t in TESTS]
    rows.sort(key=lambda r:r['test'])
    ok=all(r['returncode']==0 for r in rows)
    clean_release_residue()
    removed = cleanup_bytecode_artifacts(ROOT)
    remaining = [path.relative_to(ROOT).as_posix() for path in scan_bytecode_artifacts(ROOT)]
    ok = ok and not remaining
    report={'status':'PASS' if ok else 'FAIL','tests':len(TESTS),'rows':rows,'bytecode_cleanup_removed':len(removed),'bytecode_residue_remaining':len(remaining)}
    print(json.dumps(report, indent=2, sort_keys=True))
    if not ok: raise SystemExit(1)
if __name__=='__main__': main()
