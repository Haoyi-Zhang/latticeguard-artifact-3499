from __future__ import annotations
import csv
import json
from pathlib import Path

FORBIDDEN_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".git", ".github", "node_modules", "build", "dist"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}
PAPER_TRANSIENT_SUFFIXES = {".aux", ".bbl", ".blg", ".fdb_latexmk", ".fls", ".log", ".out", ".synctex.gz"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists(): return []
    with path.open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))



def _scan_generated_residue(package_root: Path) -> list[str]:
    errors: list[str] = []
    for path in package_root.rglob('*'):
        rel = path.relative_to(package_root).as_posix()
        if path.name in FORBIDDEN_NAMES:
            errors.append(f'generated residue present: {rel}')
        if path.is_file() and path.suffix in FORBIDDEN_SUFFIXES:
            errors.append(f'bytecode residue present: {rel}')
        if rel.startswith('paper/') and path.is_file() and any(rel.endswith(s) for s in PAPER_TRANSIENT_SUFFIXES):
            errors.append(f'latex transient present: {rel}')
    return errors

def package_gate(root: Path) -> dict:
    res = root / 'results'
    package_rows = _read_csv(res / 'artifact_manifest.csv')
    sync_rows = _read_csv(res / 'github_sync_manifest.csv')
    errors=[]
    errors.extend(_scan_generated_residue(root.parent))
    if package_rows:
        included = [r for r in package_rows if r.get('included') == 'true']
        if not included: errors.append('package manifest has no included files')
        if any(not (r['path'].startswith('artifact/') or r['path'].startswith('paper/')) for r in included): errors.append('package manifest includes paths outside artifact/ or paper/')
        if any('subjects/fixtures/' in r['path'] and r.get('included') == 'true' for r in package_rows): errors.append('generated fixtures included in artifact package manifest')
    if any('subjects/fixtures/' in r.get('path','') for r in sync_rows): errors.append('generated fixtures included in github sync manifest')
    main = root.parent / 'paper' / 'main.pdf'
    supp = root.parent / 'paper' / 'supplement.pdf'
    if not main.exists(): errors.append('missing paper/main.pdf')
    if not supp.exists(): errors.append('missing paper/supplement.pdf')
    return {'status':'PASS' if not errors else 'FAIL', 'errors':errors, 'package_rows':len(package_rows), 'sync_rows':len(sync_rows)}
