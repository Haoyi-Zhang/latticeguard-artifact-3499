from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

@dataclass(frozen=True)
class UpstreamBenchmarkAudit:
    source_id: str
    family: str
    fixture_count: int
    selftest_count: int
    selftest_failures: int
    source_urls: str
    raw_hash: str
    verdict: str


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8', newline='') as handle:
        return list(csv.DictReader(handle))


def upstream_rows(source_manifest: Path, native_selftests: Path) -> list[UpstreamBenchmarkAudit]:
    manifest = read_csv(source_manifest)
    tests = read_csv(native_selftests)
    fixture_rows = [r for r in manifest if r.get('kind') == 'native_public_fixture']
    by_source: dict[str, list[dict[str, str]]] = {}
    for row in fixture_rows:
        sid = row['source_id'].replace('_model.conf','').replace('_policy.csv','').replace('_policy.cedar','').replace('_entities.json','')
        by_source.setdefault(sid, []).append(row)
    tests_by_source: dict[str, list[dict[str, str]]] = {}
    for row in tests:
        tests_by_source.setdefault(row.get('native_fixture_ids',''), []).append(row)
    out=[]
    for sid, rows in sorted(by_source.items()):
        family = rows[0].get('adapter_id','unknown')
        st = tests_by_source.get(sid, [])
        failures = sum(1 for row in st if row.get('status') != 'PASS')
        urls = ';'.join(sorted({r.get('source_url','') for r in rows}))
        raw_hash = sha256_text(''.join(sorted(r.get('sha256','') for r in rows)))
        verdict = 'PASS' if len(rows) >= 2 and st and failures == 0 else 'FAIL'
        out.append(UpstreamBenchmarkAudit(sid, family, len(rows), len(st), failures, urls, raw_hash, verdict))
    return out


def as_csv_rows(audits: Iterable[UpstreamBenchmarkAudit]) -> list[dict[str, str]]:
    return [{
        'source_id': a.source_id,
        'family': a.family,
        'fixture_count': str(a.fixture_count),
        'selftest_count': str(a.selftest_count),
        'selftest_failures': str(a.selftest_failures),
        'source_urls': a.source_urls,
        'raw_hash': a.raw_hash,
        'verdict': a.verdict,
    } for a in audits]
