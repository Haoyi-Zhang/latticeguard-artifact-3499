#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.manuscript_presentation_gate import write_manuscript_presentation_gate


def main() -> None:
    summary = write_manuscript_presentation_gate(ROOT)
    errors: list[str] = []
    if summary.get("status") != "PASS":
        errors.append("manuscript presentation gate status is not PASS")
    if int(summary.get("presentation_checks", 0)) < 9:
        errors.append("presentation gate has too few checks")
    report = {"status": "PASS" if not errors else "FAIL", "errors": errors, **summary}
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
