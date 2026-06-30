#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.open_science_compliance_gate import write_open_science_compliance_gate


def main() -> None:
    report = write_open_science_compliance_gate(ROOT)
    errors: list[str] = []
    if report.get("status") != "PASS":
        errors.append("open science compliance gate status is not PASS")
    if int(report.get("open_science_checks", 0)) < 6:
        errors.append("open science compliance gate has too few checks")
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors, **report}, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
