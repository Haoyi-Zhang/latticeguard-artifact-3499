#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.reproducibility_risk_check import write_reproducibility_risk_check


def main() -> None:
    report = write_reproducibility_risk_check(ROOT)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report.get("status") != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
