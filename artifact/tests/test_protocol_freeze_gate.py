from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from latticeguard.protocol_freeze_gate import write_protocol_freeze_gate


def test_protocol_freeze_gate_passes() -> None:
    report = write_protocol_freeze_gate(ROOT)
    assert report["status"] == "PASS"
    assert report["checks"] >= 10
