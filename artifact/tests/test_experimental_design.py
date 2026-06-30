from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from latticeguard.experimental_design import AUDIT_QUESTIONS

def test_audit_questions_cover_design_streams():
    assert 'primary_real_adapter_obligations' in AUDIT_QUESTIONS
    assert 'bounded_core_law_certificate' in AUDIT_QUESTIONS
    assert len(AUDIT_QUESTIONS) >= 7
