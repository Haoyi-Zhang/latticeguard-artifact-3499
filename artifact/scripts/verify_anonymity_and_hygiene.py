#!/usr/bin/env python3
"""Anonymous artifact hygiene verifier."""
from __future__ import annotations
import sys

sys.dont_write_bytecode = True

import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
BANNED_PATH_PARTS = {"__pycache__", ".ipynb_checkpoints"}
BANNED_SUFFIXES = {".aux", ".bbl", ".blg", ".log", ".out", ".synctex", ".synctex.gz", ".fls", ".fdb_latexmk"}
TEXT_SUFFIXES = {".tex", ".md", ".csv", ".json", ".py", ".cff", ".txt"}
ALLOW_TERM_FILES = {"paper/IEEEtran.cls"}
GENERATED_PREFIXES = ("artifact/subjects/fixtures/",)

def _s(vals: list[int]) -> str:
    return "".join(map(chr, vals))

LOCAL_ROOTS = ["home", "Users", "mnt", "tmp", "var/folders", "private/tmp", "workspace", "root"]
LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9])/(?:" + "|".join(re.escape(x) for x in LOCAL_ROOTS) + r")/[^\s\"',)]+")
PROCESS_PATTERNS = [
    _s([67,104,97,116,71,80,84]),
    _s([99,111,110,118,101,114,115,97,116,105,111,110,32,116,114,97,110,115,99,114,105,112,116]),
    _s([109,121,102,105,108,101,115,95,98,114,111,119,115,101,114]),
    _s([76,97,116,116,105,99,101,71,117,97,114,100,95,67,111,110,116,105,110,117,97,116,105,111,110,95,80,114,111,109,112,116]),
]
BANNED_LITERAL_PATTERNS = [
    _s([47,109,110,116,47,100,97,116,97]),
    _s([117,115,101,114,45,116,102,98,114,98,52,74,114]),
    _s([112,114,111,109,112,116,32,112,97,99,107,97,103,101]),
    _s([114,101,118,105,101,119,32,116,114,97,99,101]),
]
PROCESS_TRACE_RE = re.compile("|".join(re.escape(p) for p in PROCESS_PATTERNS), re.IGNORECASE)
AMENDMENT_LABEL_RE = re.compile(r"\bAmendment\s+[A-Z]\b")
BANNED_LITERAL_RE = re.compile("|".join(re.escape(p) for p in BANNED_LITERAL_PATTERNS), re.IGNORECASE)

def rel(path: Path) -> str:
    return str(path.relative_to(REPO))

def main() -> int:
    errors=[]
    top={p.name for p in REPO.iterdir() if p.is_dir()}
    if top != {"paper", "artifact"}:
        errors.append(f"top-level dirs must be exactly paper/artifact, got {sorted(top)}")
    for path in REPO.rglob("*"):
        r=rel(path)
        if any(part in BANNED_PATH_PARTS for part in path.parts):
            errors.append(f"cache path present: {r}")
        if path.is_file():
            if any(r.startswith(prefix) for prefix in GENERATED_PREFIXES):
                continue
            if any(r.endswith(s) for s in BANNED_SUFFIXES):
                errors.append(f"transient file present: {r}")
            if path.suffix.lower() in TEXT_SUFFIXES and r not in ALLOW_TERM_FILES:
                text=path.read_text(encoding="utf-8", errors="ignore")
                if LOCAL_PATH_RE.search(text):
                    errors.append(f"local absolute path in {r}")
                if PROCESS_TRACE_RE.search(text) or AMENDMENT_LABEL_RE.search(text):
                    errors.append(f"process trace term in {r}")
                if BANNED_LITERAL_RE.search(text):
                    errors.append(f"banned trace/local literal in {r}")
    out={"status":"FAIL" if errors else "PASS", "errors":errors, "top_level_dirs":sorted(top)}
    print(json.dumps(out, indent=2, sort_keys=True))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
