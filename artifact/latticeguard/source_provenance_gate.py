from __future__ import annotations

"""Executable corpus-provenance gate for paper-visible subject claims.

The gate separates documentation/upstream/native/stress/generated strata so the
paper can report a large frozen subject set without implying that every source
is a pristine upstream benchmark.  It is deliberately conservative: source
identifiers that look like stress witnesses are counted as stress witnesses even
when they are stored under subjects/public for replay convenience.
"""

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SUBJECTS_PUBLIC = ROOT / "subjects" / "public"
SUBJECTS_GENERATED = ROOT / "subjects" / "generated"
SUBJECTS_NATIVE = ROOT / "subjects" / "native_public"

FIELDS = [
    "stratum",
    "source_count",
    "example_ids",
    "paper_interpretation",
    "claim_safety_rule",
]


def _source_id(path: Path) -> str:
    return path.stem


def classify_source_id(source_id: str) -> str:
    if source_id.startswith("generated_"):
        return "generated_canonical_probe"
    if source_id.startswith("public_deep_") or source_id.startswith("public_matrix_"):
        return "semantic_stress_witness"
    if source_id.startswith("public_native_"):
        return "native_canonical_slice"
    if source_id.startswith("public_upstream_"):
        return "upstream_example_slice"
    if source_id.startswith("public_"):
        return "official_documentation_slice"
    return "unclassified"


def _public_subject_ids() -> list[str]:
    if not SUBJECTS_PUBLIC.exists():
        return []
    return sorted(_source_id(p) for p in SUBJECTS_PUBLIC.glob("*.json"))


def _generated_subject_ids() -> list[str]:
    if not SUBJECTS_GENERATED.exists():
        return []
    return sorted(_source_id(p) for p in SUBJECTS_GENERATED.glob("*.json"))


def _raw_native_fixture_bundles() -> int:
    if not SUBJECTS_NATIVE.exists():
        return 0
    return sum(1 for p in SUBJECTS_NATIVE.iterdir() if p.is_dir())


def build_source_provenance(root: Path = ROOT) -> tuple[list[dict[str, str]], dict[str, object]]:
    subject_ids = _public_subject_ids() + _generated_subject_ids()
    counts = Counter(classify_source_id(sid) for sid in subject_ids)
    unclassified = sorted(sid for sid in subject_ids if classify_source_id(sid) == "unclassified")
    rows = []
    descriptions = {
        "official_documentation_slice": (
            "Normalized slices transcribed from official Casbin/Cedar documentation pages.",
            "May be described as documentation-derived public semantics; not a broad upstream benchmark."
        ),
        "upstream_example_slice": (
            "Canonicalized public example/test slices from upstream project material.",
            "May be described as upstream example coverage only with hash/provenance retained."
        ),
        "native_canonical_slice": (
            "Canonical law objects translated from raw native fixture bundles after native self-tests.",
            "May be counted as native fixture imports only when raw hash and self-test linkage exist."
        ),
        "semantic_stress_witness": (
            "Deterministic stress witnesses derived from the frozen law catalog to exercise relation combinations.",
            "Must be reported as stress witnesses, not as independent upstream/public benchmark cases."
        ),
        "generated_canonical_probe": (
            "Single generated canonical law probe used to keep the generated stratum explicit.",
            "Must remain separately labeled as generated."
        ),
        "unclassified": (
            "Unknown source-id pattern.",
            "Gate failure unless empty."
        ),
    }
    for stratum in [
        "official_documentation_slice",
        "upstream_example_slice",
        "native_canonical_slice",
        "semantic_stress_witness",
        "generated_canonical_probe",
        "unclassified",
    ]:
        ids = [sid for sid in subject_ids if classify_source_id(sid) == stratum]
        if not ids and stratum != "unclassified":
            continue
        interp, rule = descriptions[stratum]
        rows.append({
            "stratum": stratum,
            "source_count": str(len(ids)),
            "example_ids": ";".join(ids[:5]),
            "paper_interpretation": interp,
            "claim_safety_rule": rule,
        })
    audited = sum(int(r["source_count"]) for r in rows if r["stratum"] != "unclassified")
    errors = []
    if unclassified:
        errors.append("unclassified subject ids: " + ";".join(unclassified[:10]))
    if counts["generated_canonical_probe"] != 1:
        errors.append("expected exactly one generated canonical probe")
    if counts["semantic_stress_witness"] <= counts["official_documentation_slice"]:
        errors.append("semantic stress witness stratum unexpectedly small")
    if counts["official_documentation_slice"] < 5:
        errors.append("official documentation slice count below minimum")
    if counts["upstream_example_slice"] < 5:
        errors.append("upstream example slice count below minimum")
    if counts["native_canonical_slice"] < 8:
        errors.append("native canonical slice count below minimum")
    if audited != len(subject_ids):
        errors.append("audited subject count mismatch")
    raw_bundles = _raw_native_fixture_bundles()
    if raw_bundles < counts["native_canonical_slice"]:
        errors.append("raw native fixture bundles fewer than native canonical slices")
    report = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "audited_subject_sources": audited,
        "official_documentation_sources": counts["official_documentation_slice"],
        "upstream_example_sources": counts["upstream_example_slice"],
        "native_canonical_sources": counts["native_canonical_slice"],
        "semantic_stress_witness_sources": counts["semantic_stress_witness"],
        "generated_sources": counts["generated_canonical_probe"],
        "raw_native_fixture_bundles": raw_bundles,
        "claim_safety": "report total as frozen subject sources; separately label documentation/upstream/native/stress/generated strata",
    }
    return rows, report


def write_source_provenance_gate(root: Path = ROOT) -> dict[str, object]:
    rows, report = build_source_provenance(root)
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "source_provenance_gate.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    (RESULTS / "source_provenance_gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(write_source_provenance_gate(ROOT), indent=2, sort_keys=True))
