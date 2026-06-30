#!/usr/bin/env python3
"""Pre-result external-tool preflight for optional adapters."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from latticeguard.opa_pinning import inspect_opa_candidate


def main() -> int:
    report = inspect_opa_candidate(ROOT)
    selected = report.get("path") if report.get("status") == "READY" else None
    tool = {"adapter_id": "opa_rego_cli", "selected": selected, "pinning_report": report}
    if selected:
        cp=subprocess.run([str(selected), "version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=False)
        tool.update({"returncode": cp.returncode, "stdout": cp.stdout.splitlines()[:5], "stderr": cp.stderr.splitlines()[:5]})
    out={"status":"PASS", "tools":{"opa_rego_cli": tool}}
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
