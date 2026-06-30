from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.reproducibility_risk_check import build_reproducibility_risk_check, write_reproducibility_risk_check


TRACKED_FILES = [
    ROOT / "results" / "reproducibility_risk_check.csv",
    ROOT / "results" / "reproducibility_risk_check.json",
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


def test_reproducibility_risk_check_closes_all_final_attack_surfaces():
    rows, report = build_reproducibility_risk_check(ROOT)
    assert len(rows) >= 12
    assert report["status"] == "PASS"
    assert report["open_risks"] == 0


def test_reproducibility_risk_check_is_persisted_as_replayable_ledger():
    snapshot = _snapshot(TRACKED_FILES)
    try:
        report = write_reproducibility_risk_check(ROOT)
        assert report["status"] == "PASS"
        assert TRACKED_FILES[0].exists()
        assert TRACKED_FILES[1].exists()
    finally:
        _restore(snapshot)
