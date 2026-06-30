from __future__ import annotations

import csv
import json
import re
from pathlib import Path

CITE_RE = re.compile(r"\\(?:cite|citep|citet|citealp|citeauthor|nocite)(?:\[[^\]]*\])*\{([^}]+)\}")
ENTRY_RE = re.compile(r"@(?P<type>\w+)\s*\{\s*(?P<key>[^,\s]+)\s*,", re.MULTILINE)
FIELD_RE = re.compile(r"(?P<name>[A-Za-z][A-Za-z0-9_\-]*)\s*=\s*(?P<value>\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\"[^\"]*\"|[^,\n]+)", re.MULTILINE)
BAD_MARKERS = {'todo', 'tbd', 'placeholder', 'unknown', 'citation needed', '????'}


def _read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace') if path.exists() else ''


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


def _strip_comments(tex: str) -> str:
    out = []
    for line in tex.splitlines():
        # Keep escaped percent signs; remove simple TeX comments.
        cut = len(line)
        i = 0
        while True:
            i = line.find('%', i)
            if i == -1:
                break
            if i == 0 or line[i - 1] != '\\':
                cut = i; break
            i += 1
        out.append(line[:cut])
    return '\n'.join(out)


def citation_keys(tex: str) -> set[str]:
    keys: set[str] = set()
    for m in CITE_RE.finditer(_strip_comments(tex)):
        for item in m.group(1).split(','):
            key = item.strip()
            if key:
                keys.add(key)
    return keys


def _entry_spans(bib: str) -> list[tuple[str, str, int, int]]:
    matches = list(ENTRY_RE.finditer(bib))
    spans = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(bib)
        spans.append((m.group('type').lower(), m.group('key'), start, end))
    return spans


def _clean_value(value: str) -> str:
    value = value.strip().rstrip(',').strip()
    if (value.startswith('{') and value.endswith('}')) or (value.startswith('"') and value.endswith('"')):
        value = value[1:-1]
    return re.sub(r"\s+", " ", value).strip()


def bib_entries(bib: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for typ, key, start, end in _entry_spans(bib):
        body = bib[start:end]
        fields = {'ENTRYTYPE': typ, 'ID': key}
        for fm in FIELD_RE.finditer(body):
            fields[fm.group('name').lower()] = _clean_value(fm.group('value'))
        entries[key] = fields
    return entries


def build_reference_rows(repo_root: Path) -> list[dict[str, object]]:
    paper = repo_root / 'paper'
    artifact = repo_root / 'artifact'
    main_tex = _read_text(paper / 'main.tex')
    supplement_tex = _read_text(paper / 'supplement.tex')
    all_cites = citation_keys(main_tex) | citation_keys(supplement_tex)
    main_cites = citation_keys(main_tex)
    supp_cites = citation_keys(supplement_tex)
    entries = bib_entries(_read_text(paper / 'references.bib'))
    crosswalk = {(r.get('key') or r.get('paper_bib_key') or ''): r for r in _read_csv(artifact / 'reference_integrity_crosswalk.csv')}
    rows: list[dict[str, object]] = []
    for key in sorted(set(entries) | all_cites):
        e = entries.get(key, {})
        title = e.get('title', '')
        doi = e.get('doi', '')
        url = e.get('url', '')
        entry_type = e.get('ENTRYTYPE', '')
        has_locator = bool(doi or url or e.get('isbn', '') or e.get('publisher', '') or e.get('booktitle', '') or e.get('journal', ''))
        bad_text = ' '.join([key, title, doi, url, entry_type]).lower()
        marker_hit = any(marker in bad_text for marker in BAD_MARKERS)
        status = 'PASS'
        reason = 'cited_bib_entry_with_locator'
        if key not in entries:
            status = 'FAIL'; reason = 'citation_missing_from_bibliography'
        elif key not in all_cites:
            status = 'FAIL'; reason = 'bibliography_entry_uncited'
        elif not title:
            status = 'FAIL'; reason = 'missing_title'
        elif not has_locator:
            status = 'FAIL'; reason = 'missing_stable_locator_or_venue_metadata'
        elif marker_hit:
            status = 'FAIL'; reason = 'placeholder_marker_detected'
        elif key not in crosswalk:
            # Crosswalk is an additional artifact-level claim ledger.  A missing
            # row is not a bibliographic failure, but it is a gateability gap.
            status = 'WARN'; reason = 'missing_reference_crosswalk_row'
        rows.append({
            'key': key,
            'entry_type': entry_type,
            'cited_in_main': str(key in main_cites).lower(),
            'cited_in_supplement': str(key in supp_cites).lower(),
            'has_title': str(bool(title)).lower(),
            'has_doi': str(bool(doi)).lower(),
            'has_url': str(bool(url)).lower(),
            'has_crosswalk_row': str(key in crosswalk).lower(),
            'status': status,
            'reason': reason,
        })
    return rows


def _reference_ledger_closure(artifact_root: Path) -> tuple[int, int]:
    rows = _read_csv(artifact_root / 'reference_ledger.csv')
    unresolved = 0
    bad_markers = {'candidate', 'verify_before', 'to verify', 'before import', 'todo', 'tbd', 'unknown', 'uncertain', 'feasibility stage', 'reconnaissance'}
    for row in rows:
        status = (row.get('status') or '').strip().lower()
        action = (row.get('bibtex_action') or '').strip().lower()
        text = ' '.join(str(v).lower() for v in row.values())
        if status != 'verified_frozen' or action != 'bibtex_frozen' or any(marker in text for marker in bad_markers):
            unresolved += 1
    return len(rows), unresolved


def summarize_reference_gate(rows: list[dict[str, object]], artifact_root: Path) -> dict[str, object]:
    failures = [r for r in rows if r.get('status') == 'FAIL']
    warnings = [r for r in rows if r.get('status') == 'WARN']
    ledger_rows, ledger_failures = _reference_ledger_closure(artifact_root)
    return {
        'status': 'PASS' if not failures and not warnings and rows and ledger_failures == 0 else 'FAIL',
        'reference_entries': len(rows),
        'failures': len(failures),
        'warnings': len(warnings),
        'cited_entries': sum(1 for r in rows if str(r.get('cited_in_main')).lower() == 'true' or str(r.get('cited_in_supplement')).lower() == 'true'),
        'crosswalk_rows_covered': sum(1 for r in rows if str(r.get('has_crosswalk_row')).lower() == 'true'),
        'reference_ledger_rows': ledger_rows,
        'reference_ledger_failures': ledger_failures,
        'evidence': 'references.bib, main.tex, supplement.tex, reference_integrity_crosswalk.csv, and reference_ledger.csv parsed locally',
    }


def write_reference_integrity_gate(artifact_root: Path) -> dict[str, object]:
    repo_root = artifact_root.parent
    rows = build_reference_rows(repo_root)
    fieldnames = ['key', 'entry_type', 'cited_in_main', 'cited_in_supplement', 'has_title', 'has_doi', 'has_url', 'has_crosswalk_row', 'status', 'reason']
    _write_csv(artifact_root / 'results' / 'reference_integrity_gate.csv', rows, fieldnames)
    summary = summarize_reference_gate(rows, artifact_root)
    _write_json(artifact_root / 'results' / 'reference_integrity_gate.json', summary)
    return summary
