from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.evidence_challenge_check import write_evidence_challenge_check


TRACKED_FILES = [
    ROOT / 'results' / 'evidence_challenge_findings.csv',
    ROOT / 'results' / 'evidence_challenge_repair_matrix.csv',
    ROOT / 'results' / 'paper_impact_matrix.csv',
    ROOT / 'results' / 'evidence_challenge_check.json',
]


def _snapshot(paths):
    return {path: path.read_bytes() if path.exists() else None for path in paths}


def _restore(snapshot):
    for path, data in snapshot.items():
        if data is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)


def test_evidence_challenge_check_closes_strict_quality_dimensions():
    snapshot = _snapshot(TRACKED_FILES)
    try:
        report = write_evidence_challenge_check(ROOT)
        assert report['status'] == 'PASS'
        assert report['quality_lenses'] >= 5
        assert report['quality_dimensions'] >= 9
        assert report['blocking_repairs_after_quality_gate'] == 0
    finally:
        _restore(snapshot)
