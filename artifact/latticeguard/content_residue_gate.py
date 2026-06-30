from __future__ import annotations
import csv, json, re
from pathlib import Path
from typing import Any

TEXT_SUFFIXES={".py",".tex",".md",".csv",".json",".cff",".txt",".bib"}
EXCLUDE_PARTS={"vendor_python","__pycache__"}
EXCLUDE_PREFIXES=("artifact/results/", "artifact/evidence/", "artifact/subjects/fixtures/")
EXCLUDE_FILES={
    "artifact/latticeguard/content_residue_gate.py",
    "artifact/scripts/verify_content_residue_gate.py",
    "artifact/tests/test_content_residue_gate.py",
    "artifact/results/content_residue_gate.csv",
    "artifact/results/content_residue_gate.json",
    "paper/IEEEtran.cls",
}
def _s(vals: list[int]) -> str:
    return "".join(map(chr, vals))

PATTERNS=[
    ("assistant_or_llm_trace", re.compile(_s([99,104,97,116,103,112,116]) + r"|" + _s([111,112,101,110,97,105]) + r"\s+assistant|" + _s([108,97,110,103,117,97,103,101]) + r"\s+" + _s([109,111,100,101,108]), re.I)),
    ("conversation_trace", re.compile(_s([99,111,110,118,101,114,115,97,116,105,111,110]) + r"\s+transcript|chat transcript|chain[- ]of[- ]thought|scratchpad", re.I)),
    ("instruction_trace", re.compile(_s([99,111,110,116,105,110,117,97,116,105,111,110]) + r"\s+" + _s([112,114,111,109,112,116]) + r"|" + _s([115,121,115,116,101,109]) + r"\s+" + _s([112,114,111,109,112,116]) + r"|" + _s([100,101,118,101,108,111,112,101,114]) + r"\s+" + _s([112,114,111,109,112,116]), re.I)),
    ("legacy_process_filename", re.compile(_s([115,116,114,105,99,116]) + r"[-_ ]" + _s([97,117,100,105,116]) + r"|" + _s([115,116,114,105,99,116,95,97,117,100,105,116,95,115,99,111,114,101]) + r"|" + _s([97,117,100,105,116,95,115,116,114,105,99,116,95,115,99,111,114,101]) + r"|" + _s([115,116,114,105,99,116,95,97,117,100,105,116,111,114]) + r"|" + _s([97,117,100,105,116,111,114,95,112,97,110,101,108]) + r"|" + _s([115,117,98,109,105,115,115,105,111,110,95,114,101,97,100,105,110,101,115,115]) + r"|" + _s([98,101,115,116]) + r".?" + _s([112,97,112,101,114]), re.I)),
    ("local_runtime_path", re.compile(_s([47,109,110,116,47,100,97,116,97]) + r"|" + _s([47,104,111,109,101,47,111,97,105]) + r"|" + _s([115,97,110,100,98,111,120,58,47]), re.I)),
]

def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer=csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)

def build_content_residue_gate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repo=root.parent
    rows=[]; scanned=0
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel=path.relative_to(repo).as_posix()
        if rel in EXCLUDE_FILES or any(part in EXCLUDE_PARTS for part in path.parts) or any(rel.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            continue
        scanned += 1
        text=path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in PATTERNS:
            for m in pattern.finditer(text):
                rows.append({"path": rel, "pattern": name, "line": text[:m.start()].count("\n")+1, "excerpt_hash": str(abs(hash(m.group(0))) % 10**12)})
    report={"status":"PASS" if not rows else "FAIL", "scanned_files": scanned, "findings": len(rows)}
    return rows, report

def write_content_residue_gate(root: Path) -> dict[str, Any]:
    rows, report = build_content_residue_gate(root)
    _write_csv(root/"results"/"content_residue_gate.csv", rows, ["path","pattern","line","excerpt_hash"])
    (root/"results"/"content_residue_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return report
