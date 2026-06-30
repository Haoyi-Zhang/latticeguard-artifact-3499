from __future__ import annotations
import csv, json
from pathlib import Path

def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def design_matrix(root: Path) -> list[dict[str, object]]:
    results = root / 'results'
    summary = json.loads((results/'summary.json').read_text(encoding='utf-8'))
    rows = []
    for stream, metric in [
        ('primary_real_adapter_obligations','primary_evaluated_obligations'),
        ('invalid_transformation_rejections','rejected_invalid_transformations'),
        ('unsupported_fragment_accounting','unsupported_transformations'),
        ('seeded_semantic_drift_controls','seeded_mutant_rows'),
        ('minimized_counterexample_replay','minimized_counterexamples'),
        ('bounded_core_law_certificate','bounded_model_checked_cases'),
        ('native_fixture_selftests','native_selftest_rows'),
    ]:
        rows.append({'stream': stream, 'metric': metric, 'value': summary.get(metric, 0), 'audit_question': AUDIT_QUESTIONS[stream]})
    return rows

AUDIT_QUESTIONS = {
    'primary_real_adapter_obligations': 'Do real local adapters execute the counted law obligations?',
    'invalid_transformation_rejections': 'Can invalid transformations inflate the denominator?',
    'unsupported_fragment_accounting': 'Are unsupported language fragments visible rather than hidden?',
    'seeded_semantic_drift_controls': 'Does the oracle kill known semantic-drift mutants?',
    'minimized_counterexample_replay': 'Are failures reduced to replayable semantic slices?',
    'bounded_core_law_certificate': 'Are law predicates checked against an executable core model?',
    'native_fixture_selftests': 'Are native-format benchmark files exercised before normalization?',
}
