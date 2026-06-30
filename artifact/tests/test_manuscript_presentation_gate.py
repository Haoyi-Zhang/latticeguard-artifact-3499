from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.manuscript_presentation_gate import build_manuscript_presentation_gate


def test_manuscript_presentation_gate_passes_current_packet():
    rows, report = build_manuscript_presentation_gate(ROOT)
    assert len(rows) >= 9
    assert report["status"] == "PASS", report
    assert report["failures"] == 0
