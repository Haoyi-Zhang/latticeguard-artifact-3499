#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from latticeguard.module_import_gate import write_module_import_gate

def main() -> None:
    report=write_module_import_gate(ROOT)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report.get("status") != "PASS": raise SystemExit(1)
if __name__=="__main__": main()
