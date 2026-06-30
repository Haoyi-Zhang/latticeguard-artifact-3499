from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Objection:
    lens: str
    objection: str
    evidence_file: str
    repair_status: str
    residual_risk: str

DEFAULT_OBJECTIONS = [
    Objection('artifact_reproducibility','Can an assessor replay every paper-visible count from the clean repository?','results/claim_verification.json','closed_by_verify_full_claims','Low if artifact root is preserved.'),
    Objection('formal_soundness','Are access-control laws checked beyond hand-picked examples?','results/model_check_summary.json','closed_by_bounded_model_check','Bounded model check is not an unbounded theorem.'),
    Objection('applicability_discipline','Are invalid transformations rejected rather than counted as passes?','results/predicate_evaluations.csv','closed_by_predicate_engine','Low; verifier checks witness rows.'),
    Objection('benchmark_provenance','Are native upstream fixture files more than labels?','results/native_selftest_results.csv','closed_by_native_selftests','Medium until broad upstream suites are counted.'),
    Objection('counterexample_replay','Can seeded drift witnesses be minimized and replayed?','results/counterexamples.json','closed_by_minimization_replay','Low for seeded controls; real drift mining remains separate.'),
    Objection('repository_hygiene','Does the repository contain process traces, local paths, or transient build outputs?','results/repository_scorecard.json','closed_by_hygiene_verifier','Low for clean packet.'),
]

def objection_rows(summary_path: Path | None = None) -> list[dict[str, str]]:
    rows=[o.__dict__ for o in DEFAULT_OBJECTIONS]
    if summary_path and summary_path.exists():
        summary=json.loads(summary_path.read_text(encoding='utf-8'))
        rows.append({'lens':'scale','objection':'Is the evaluation too small to stress the oracle?','evidence_file':'results/summary.json','repair_status':f"{summary.get('primary_evaluated_obligations')} primary obligations over {summary.get('source_ids_covered')} sources",'residual_risk':'OPA and real release drift require a future counted run.'})
    return rows
