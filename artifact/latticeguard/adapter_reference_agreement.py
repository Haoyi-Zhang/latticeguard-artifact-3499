from __future__ import annotations

import csv
import json
from pathlib import Path


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


def build_agreement_rows(root: Path) -> list[dict[str, object]]:
    """Compare every counted adapter decision against the executable reference semantics.

    The law invariant can pass even when both before/after adapter decisions move
    together.  This ledger closes that gateer attack surface by checking the
    normalized adapter bridge directly: for each applicable row, the adapter's
    before and after decisions must equal the corresponding reference decisions
    emitted by soundness_checks.csv for the same candidate_id.
    """
    results = root / 'results'
    obligations = _read_csv(results / 'obligations.csv')
    soundness = {r['candidate_id']: r for r in _read_csv(results / 'soundness_checks.csv')}
    rows: list[dict[str, object]] = []
    for r in obligations:
        if r.get('applicability_status') != 'APPLICABLE_EVALUATED':
            continue
        ref = soundness.get(r.get('candidate_id', ''), {})
        before_ref = ref.get('before_reference_decision', '')
        after_ref = ref.get('after_reference_decision', '')
        before_ok = r.get('before_decision') == before_ref
        after_ok = r.get('after_decision') == after_ref
        status = 'PASS' if before_ok and after_ok else 'FAIL'
        rows.append({
            'row_id': r.get('row_id', ''),
            'adapter_id': r.get('adapter_id', ''),
            'source_id': r.get('source_id', ''),
            'relation_id': r.get('relation_id', ''),
            'candidate_id': r.get('candidate_id', ''),
            'before_adapter_decision': r.get('before_decision', ''),
            'before_reference_decision': before_ref,
            'after_adapter_decision': r.get('after_decision', ''),
            'after_reference_decision': after_ref,
            'before_agrees': str(before_ok).lower(),
            'after_agrees': str(after_ok).lower(),
            'status': status,
        })
    rows.sort(key=lambda x: (str(x['adapter_id']), str(x['source_id']), str(x['relation_id']), str(x['candidate_id']), str(x['row_id'])))
    return rows


def summarize_agreement(rows: list[dict[str, object]]) -> dict[str, object]:
    failures = [r for r in rows if r.get('status') != 'PASS']
    return {
        'status': 'PASS' if not failures and rows else 'FAIL',
        'rows_checked': len(rows),
        'failures': len(failures),
        'adapters_covered': len({str(r.get('adapter_id', '')) for r in rows}),
        'relations_covered': len({str(r.get('relation_id', '')) for r in rows}),
        'sources_covered': len({str(r.get('source_id', '')) for r in rows}),
        'evidence': 'adapter before/after decisions joined with soundness_checks reference decisions by candidate_id',
    }


def write_adapter_reference_agreement(root: Path) -> dict[str, object]:
    rows = build_agreement_rows(root)
    fieldnames = [
        'row_id', 'adapter_id', 'source_id', 'relation_id', 'candidate_id',
        'before_adapter_decision', 'before_reference_decision',
        'after_adapter_decision', 'after_reference_decision',
        'before_agrees', 'after_agrees', 'status',
    ]
    _write_csv(root / 'results' / 'adapter_reference_agreement.csv', rows, fieldnames)
    summary = summarize_agreement(rows)
    _write_json(root / 'results' / 'adapter_reference_agreement.json', summary)
    return summary
