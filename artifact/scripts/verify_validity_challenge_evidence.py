#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from latticeguard.validity_challenge_evidence import write_validity_challenge_evidence


def main() -> None:
    report = write_validity_challenge_evidence(ROOT)
    errors: list[str] = []
    if report.get("status") != "PASS":
        errors.append("validity challenge evidence status is not PASS")
    if int(report.get("checks", 0)) < 7:
        errors.append("too few validity challenge checks")
    if report.get("opa_native_closure_claimed") is not False:
        errors.append("OPA native closure claim must remain false")
    if int(report.get("holdout_relation_count", 0)) != 12:
        errors.append("holdout split must cover all relation families")
    if int(report.get("holdout_adapter_count", 0)) != 3:
        errors.append("holdout split must cover all counted adapters")
    if int(report.get("raw_native_fixture_bundles", 0)) < int(report.get("stress_witness_sources", 0)):
        errors.append("raw native fixture bundles must cover stress witness count")
    final = {"status": "PASS" if not errors else "FAIL", "errors": errors, **report}
    print(json.dumps(final, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
