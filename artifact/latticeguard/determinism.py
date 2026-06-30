from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
from typing import Any

def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def digest(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode()).hexdigest()

def csv_digest(path: Path) -> str:
    with path.open('r', encoding='utf-8', newline='') as f:
        rows=list(csv.DictReader(f))
    return digest(rows)

def ledger_digest(root: Path) -> str:
    rows=[]
    with (root/'evidence'/'SHA256SUMS.csv').open('r', encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f): rows.append((r['path'], r['sha256']))
    return digest(rows)

def assert_sorted_csv(path: Path, key_fields: list[str]) -> bool:
    with path.open('r', encoding='utf-8', newline='') as f:
        rows=list(csv.DictReader(f))
    keys=[tuple(r.get(k,'') for k in key_fields) for r in rows]
    return keys == sorted(keys)
