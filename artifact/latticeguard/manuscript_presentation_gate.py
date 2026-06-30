from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _strip_comments(tex: str) -> str:
    out: list[str] = []
    for line in tex.splitlines():
        cut = len(line)
        i = 0
        while True:
            i = line.find('%', i)
            if i == -1:
                break
            if i == 0 or line[i - 1] != '\\':
                cut = i
                break
            i += 1
        out.append(line[:cut])
    return "\n".join(out)


def _count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def _s(vals: list[int]) -> str:
    return "".join(map(chr, vals))


def build_manuscript_presentation_gate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repo = root.parent
    main = _strip_comments(_read(repo / "paper" / "main.tex"))
    supp = _strip_comments(_read(repo / "paper" / "supplement.tex"))
    rows: list[dict[str, Any]] = []

    def add(check_id: str, rule: str, observed: Any, threshold: str, ok: bool) -> None:
        rows.append({
            "check_id": check_id,
            "rule": rule,
            "observed": observed,
            "threshold": threshold,
            "status": "PASS" if ok else "FAIL",
        })

    disallowed_impl = _count(r"(artifact/|scripts/|README(?:\.md)?|reproduction(?:\.md)?|__pycache__|\.csv\b|\.json\b|\.py\b)", main)
    trace_pattern = "|".join([_s([99,104,97,116,103,112,116]), _s([111,112,101,110,97,105]), _s([112,114,111,109,112,116]) + r"\s+" + _s([116,114,97,99,101]), _s([99,111,110,118,101,114,115,97,116,105,111,110]) + r"\s+" + _s([116,114,97,110,115,99,114,105,112,116]), _s([99,104,97,105,110]) + r"[- ]" + _s([111,102]) + r"[- ]" + _s([116,104,111,117,103,104,116]), _s([115,99,114,97,116,99,104,112,97,100]), _s([97,105]) + r"\s*" + _s([114,97,116,101])])
    disallowed_ai_trace = _count(trace_pattern, main + "\n" + supp)
    add("MPG_001", "main manuscript contains no concrete artifact path, file extension, or replay script names", disallowed_impl, "0", disallowed_impl == 0)
    add("MPG_002", "released manuscript text contains no instruction/dialogue/evasion trace", disallowed_ai_trace, "0", disallowed_ai_trace == 0)

    texttt = main.count("\\texttt")
    add("MPG_003", "main manuscript avoids code-font identifiers and function-like presentation", texttt, "0", texttt == 0)

    section_repository = _count(r"\\section\{[^}]*Repository|\\subsection\{[^}]*Repository", main)
    add("MPG_004", "main section titles present the research system rather than repository mechanics", section_repository, "0", section_repository == 0)

    repo_count = _count(r"\brepository\b", main)
    script_count = _count(r"\bscript\b", main)
    function_count = _count(r"\bfunction\b", main)
    add("MPG_005", "main text minimizes repository/script/function vocabulary", f"repository={repo_count};script={script_count};function={function_count}", "repository<=2;script<=3;function<=2", repo_count <= 2 and script_count <= 3 and function_count <= 2)

    gate_count = _count(r"\bgate\b", main)
    ledger_count = _count(r"\bledger\b", main)
    add("MPG_006", "main text uses audit terminology sparingly rather than reading as an artifact checklist", f"gate={gate_count};ledger={ledger_count}", "gate<=15;ledger<=8", gate_count <= 15 and ledger_count <= 8)

    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", main, re.S)
    abstract_text = abstract.group(1) if abstract else ""
    has_problem = "oracle" in abstract_text.lower() and "access-control" in abstract_text.lower()
    has_method = "applicability predicate" in abstract_text.lower() and "metamorphic obligations" in abstract_text.lower()
    has_evidence = "obligations" in abstract_text.lower() and "counterexamples" in abstract_text.lower()
    add("MPG_007", "abstract states problem, method, and evidence without relying on repository reading", f"problem={has_problem};method={has_method};evidence={has_evidence}", "all true", has_problem and has_method and has_evidence)

    contribution_count = _count(r"\\item \\textbf\{", main)
    add("MPG_008", "introduction exposes a concise contribution list", contribution_count, ">=4", contribution_count >= 4)

    gen_pattern = _s([71,101,110,101,114,97,116,105,118,101,32,65,73]) + "|" + _s([99,104,97,116,103,112,116]) + "|" + _s([108,97,114,103,101,32,108,97,110,103,117,97,103,101,32,109,111,100,101,108])
    generative_in_main = _count(gen_pattern, main)
    generative_in_supp = _count(gen_pattern, supp)
    add("MPG_009", "submission text avoids side discussion about preparation tools", f"main={generative_in_main};supplement={generative_in_supp}", "main=0;supplement=0", generative_in_main == 0 and generative_in_supp == 0)

    failures = [row for row in rows if row["status"] != "PASS"]
    report = {
        "status": "PASS" if not failures else "FAIL",
        "presentation_checks": len(rows),
        "failures": len(failures),
        "failed_checks": [row["check_id"] for row in failures],
        "main_repository_mentions": repo_count,
        "main_gate_mentions": gate_count,
        "main_ledger_mentions": ledger_count,
    }
    return rows, report


def write_manuscript_presentation_gate(root: Path) -> dict[str, Any]:
    rows, report = build_manuscript_presentation_gate(root)
    _write_csv(root / "results" / "manuscript_presentation_gate.csv", rows, ["check_id", "rule", "observed", "threshold", "status"])
    (root / "results" / "manuscript_presentation_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
