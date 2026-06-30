#!/usr/bin/env python3
"""Create an anonymous artifact bundle with only paper/ and artifact/.

Generated adapter fixture material under artifact/subjects/fixtures is excluded
because scripts/run_full_evaluation.py regenerates it deterministically.  Keeping
it out of the release zip prevents tens of thousands of generated files from
being mistaken for authored repository content while retaining all deterministic
ledgers and replay scripts.
"""
from __future__ import annotations
import sys

sys.dont_write_bytecode = True

import argparse
import csv
import json
import zipfile
from pathlib import Path

ARTIFACT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ARTIFACT_ROOT.parents[0]
EXCLUDED_DIR_PARTS = {"__pycache__", ".ipynb_checkpoints"}
EXCLUDED_SUFFIXES = {".aux", ".bbl", ".blg", ".log", ".out", ".synctex", ".pyc"}
EXCLUDED_PREFIXES = ("artifact/subjects/fixtures/",)


def include(path: Path) -> tuple[bool, str]:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if path.is_dir():
        return False, "directory"
    if rel.split("/")[0] not in {"artifact", "paper"}:
        return False, "outside_top_level"
    if any(part in EXCLUDED_DIR_PARTS for part in path.parts):
        return False, "cache"
    if path.suffix in EXCLUDED_SUFFIXES:
        return False, "transient"
    if any(rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False, "generated_fixture_regenerated_by_replay"
    if rel.endswith(".zip"):
        return False, "nested_zip"
    return True, "included"


def count_generated_fixtures() -> int:
    fixture_root = REPO_ROOT / "artifact" / "subjects" / "fixtures"
    if not fixture_root.exists():
        return 0
    return sum(1 for p in fixture_root.rglob("*") if p.is_file())


def build_manifest() -> list[dict[str, object]]:
    rows = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        ok, reason = include(path)
        if reason == "generated_fixture_regenerated_by_replay":
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        rows.append({"path": rel, "bytes": path.stat().st_size, "included": str(ok).lower(), "reason": reason})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    rows = build_manifest()
    manifest_path = ARTIFACT_ROOT / "results" / "artifact_manifest.csv"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "bytes", "included", "reason"])
        w.writeheader(); w.writerows(rows)
    # Rebuild rows after writing the manifest so the manifest includes itself.
    rows = build_manifest()
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "bytes", "included", "reason"])
        w.writeheader(); w.writerows(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for row in rows:
            if row["included"] == "true":
                zf.write(REPO_ROOT / str(row["path"]), str(row["path"]))
    report = {
        "status": "PASS",
        "zip": str(args.output),
        "included_files": sum(1 for r in rows if r["included"] == "true"),
        "excluded_generated_fixtures": count_generated_fixtures(),
        "top_level": ["artifact", "paper"],
        "manifest": "artifact/results/artifact_manifest.csv",
    }
    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
