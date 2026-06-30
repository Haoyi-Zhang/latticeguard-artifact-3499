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
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def _section_text(tex: str, section: str) -> str:
    m = re.search(r"\\section\*?\{" + re.escape(section) + r"\}(.*?)(?=\\section\*?\{|\\clearpage|\\bibliographystyle|\\bibliography|\\end\{document\})", tex, re.S)
    return m.group(1) if m else ""


def _availability_text(tex: str) -> tuple[str, int]:
    section = _section_text(tex, "Data Availability")
    if section:
        positions = [
            pos for pos in (
                tex.find("\\section{Data Availability}"),
                tex.find("\\section*{Data Availability}"),
            )
            if pos >= 0
        ]
        return section, min(positions) if positions else -1
    m = re.search(r"\\noindent\\emph\{Availability\.\}(.*?)(?=\\bibliographystyle|\\bibliography|\\end\{document\})", tex, re.S)
    if m:
        return m.group(1), m.start()
    return "", -1


def build_open_science_compliance_gate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repo = root.parent
    main = _strip_comments(_read(repo / "paper" / "main.tex"))
    supp = _strip_comments(_read(repo / "paper" / "supplement.tex"))
    data, data_pos = _availability_text(main)
    rows: list[dict[str, Any]] = []

    def add(check_id: str, rule: str, observed: Any, ok: bool) -> None:
        rows.append({"check_id": check_id, "rule": rule, "observed": observed, "status": "PASS" if ok else "FAIL"})

    ref_pos = main.find("\\bibliographystyle")
    conclusion_positions = [pos for pos in [main.find("\\section{Threats, Ethics, and Conclusion}"), main.find("\\section{Conclusion}")] if pos >= 0]
    conclusion_pos = min(conclusion_positions) if conclusion_positions else -1
    add("OSC_001", "main paper contains an Availability statement", data_pos, data_pos >= 0)
    add("OSC_002", "Availability appears after conclusion/threats and before references", f"conclusion={conclusion_pos};data={data_pos};refs={ref_pos}", conclusion_pos >= 0 and data_pos > conclusion_pos and (ref_pos < 0 or data_pos < ref_pos))
    lower_data = data.lower()
    required_terms = ["anonymous", "source code", "frozen subject", "reproduce", "private data", "open-source license"]
    missing = [term for term in required_terms if term not in lower_data]
    add("OSC_003", "Data Availability states anonymized package contents, reproducibility, privacy boundary, and release intent", ";".join(missing) or "all_terms_present", not missing)
    add("OSC_004", "supplement remains anonymous and has no acknowledgement section", f"ack={supp.lower().count('acknowledg')};anonymous={supp.count('Anonymous')}", "\\section*{Acknowledg" not in supp and "Anonymous" in supp)
    add("OSC_005", "Data Availability names long-term preservation beyond the version-control mirror", f"zenodo={'zenodo' in lower_data};archive={'archival' in lower_data or 'preservation' in lower_data}", "zenodo" in lower_data and ("archival" in lower_data or "preservation" in lower_data))
    add("OSC_006", "main paper does not include acknowledgements or author-identifying disclosure", f"ack={main.lower().count('acknowledg')};author placeholders={main.count('Anonymous Author')}", "\\section*{Acknowledg" not in main and "Anonymous Author" in main)

    failures = [row for row in rows if row["status"] != "PASS"]
    report = {
        "status": "PASS" if not failures else "FAIL",
        "open_science_checks": len(rows),
        "failures": len(failures),
        "failed_checks": [row["check_id"] for row in failures],
    }
    return rows, report


def write_open_science_compliance_gate(root: Path) -> dict[str, Any]:
    rows, report = build_open_science_compliance_gate(root)
    _write_csv(root / "results" / "open_science_compliance_gate.csv", rows, ["check_id", "rule", "observed", "status"])
    (root / "results" / "open_science_compliance_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
