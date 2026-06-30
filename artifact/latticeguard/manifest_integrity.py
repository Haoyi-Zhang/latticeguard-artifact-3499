from __future__ import annotations
import csv, hashlib
from pathlib import Path

def sha256_file(path: Path) -> str:
    h=hashlib.sha256();
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def verify_sha_manifest(root: Path) -> list[str]:
    errors=[]; p=root/'evidence'/'SHA256SUMS.csv'
    if not p.exists(): return ['missing SHA256SUMS.csv']
    with p.open('r', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            path=root/r['path']
            if not path.exists(): errors.append('missing tracked file '+r['path'])
            elif sha256_file(path)!=r['sha256']: errors.append('hash mismatch '+r['path'])
    return errors
