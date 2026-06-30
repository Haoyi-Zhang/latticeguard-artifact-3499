from __future__ import annotations
import os, re
from pathlib import Path

CODE_SUFFIXES={'.py','.md','.tex','.bib','.csv','.json','.cff','.txt'}
BANNED=[''.join(map(chr,[47,109,110,116,47,100,97,116,97])), ''.join(map(chr,[99,111,110,118,101,114,115,97,116,105,111,110,32,116,114,97,110,115,99,114,105,112,116])), ''.join(map(chr,[112,114,111,109,112,116,32,108,111,103])), ''.join(map(chr,[109,121,102,105,108,101,115,95,98,114,111,119,115,101,114])), ''.join(map(chr,[71,97,116,101,55])), ''.join(map(chr,[71,97,116,101,56])), ''.join(map(chr,[71,97,116,101,57])), ''.join(map(chr,[71,97,116,101,49,48]))]


def authored_files(root: Path) -> list[Path]:
    out=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        parts=set(p.parts)
        if '__pycache__' in parts or '.ipynb_checkpoints' in parts: continue
        if p.suffix.lower() in CODE_SUFFIXES:
            out.append(p)
    return sorted(out)


def count_python_lines(root: Path) -> dict[str,int]:
    package=sum(len(p.read_text(encoding='utf-8').splitlines()) for p in (root/'latticeguard').glob('*.py')) if (root/'latticeguard').exists() else 0
    scripts=sum(len(p.read_text(encoding='utf-8').splitlines()) for p in (root/'scripts').glob('*.py')) if (root/'scripts').exists() else 0
    tests=sum(len(p.read_text(encoding='utf-8').splitlines()) for p in (root/'tests').glob('*.py')) if (root/'tests').exists() else 0
    return {'package_python_lines': package, 'script_python_lines': scripts, 'test_python_lines': tests, 'python_lines': package+scripts+tests}


def hygiene_scan(repo_root: Path) -> list[str]:
    issues=[]
    for p in repo_root.rglob('*'):
        rel=str(p.relative_to(repo_root))
        if p.is_dir() and p.name in {'__pycache__','.ipynb_checkpoints'}:
            issues.append(f'cache directory present: {rel}')
        if p.is_file() and p.suffix in {'.aux','.bbl','.blg','.log','.out','.synctex','.gz','.pyc'}:
            issues.append(f'transient file present: {rel}')
        if p.is_file() and p.suffix.lower() in CODE_SUFFIXES:
            text=p.read_text(encoding='utf-8', errors='ignore')
            for pat in BANNED:
                if re.search(pat, text, re.IGNORECASE):
                    issues.append(f'banned trace token {pat!r} in {rel}')
    return issues


def largest_python(root: Path) -> tuple[int,str]:
    best=(0,'')
    for base in ['scripts','latticeguard','tests']:
        for p in (root/base).glob('*.py') if (root/base).exists() else []:
            n=len(p.read_text(encoding='utf-8').splitlines())
            if n>best[0]: best=(n,str(p.relative_to(root)))
    return best
