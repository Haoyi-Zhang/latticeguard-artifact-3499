from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

Decision = str


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def role_closure(policy: Mapping[str, Any], principal: str, *, use_hierarchy: bool = True) -> set[str]:
    roles = set(policy.get("user_roles", {}).get(principal, []))
    if not use_hierarchy:
        return roles
    changed = True
    while changed:
        changed = False
        for role in sorted(list(roles)):
            for parent in policy.get("roles", {}).get(role, {}).get("inherits", []):
                if parent not in roles:
                    roles.add(parent)
                    changed = True
    return roles


def _matching_rules(policy: Mapping[str, Any], req: Mapping[str, Any], *, use_hierarchy: bool = True) -> list[Mapping[str, Any]]:
    reachable = role_closure(policy, str(req["principal"]), use_hierarchy=use_hierarchy)
    return [
        rule for rule in policy.get("rules", [])
        if rule.get("role") in reachable
        and rule.get("action") == req.get("action")
        and rule.get("resource") == req.get("resource")
    ]


def reference_decision(policy: Mapping[str, Any], req: Mapping[str, Any], *, use_hierarchy: bool = True) -> Decision:
    matching = _matching_rules(policy, req, use_hierarchy=use_hierarchy)
    if any(rule.get("effect") == "deny" for rule in matching):
        return "DENY"
    if any(rule.get("effect") == "allow" for rule in matching):
        return "ALLOW"
    return "DENY"


def _rewrite_policy_for_mutant(policy: Mapping[str, Any], mutant: str) -> dict[str, Any]:
    p = json.loads(stable_json(policy))
    rules = []
    for rule in p.get("rules", []):
        effect = rule.get("effect")
        if mutant in {"strip_denies", "ignore_forbid", "strip_forbid"} and effect == "deny":
            continue
        if mutant in {"strip_allows", "strip_permits"} and effect == "allow":
            continue
        r = dict(rule)
        if mutant == "invert_effects":
            r["effect"] = "deny" if effect == "allow" else "allow"
        rules.append(r)
    p["rules"] = rules
    return p


def mutant_decision(adapter_id: str, policy: Mapping[str, Any], req: Mapping[str, Any]) -> Decision:
    """Independent semantic model of the seeded drift adapters.

    This is deliberately smaller than the executable adapters in run_full_evaluation.py.
    It replays only the mutation semantics used to produce positive controls,
    making counterexample checking independent of fixture rendering, Casbin files,
    Cedar files, and object identity.
    """
    mutant = adapter_id.split("_mutant_", 1)[1] if "_mutant_" in adapter_id else "normal"
    use_hierarchy = mutant != "no_hierarchy"
    p = _rewrite_policy_for_mutant(policy, mutant)
    if mutant == "allow_overrides":
        matching = _matching_rules(p, req, use_hierarchy=use_hierarchy)
        return "ALLOW" if any(rule.get("effect") == "allow" for rule in matching) else "DENY"
    decision = reference_decision(p, req, use_hierarchy=use_hierarchy)
    if mutant == "default_allow" and decision == "DENY":
        return "ALLOW"
    return decision


def invariant_holds(invariant: str, before: Decision, after: Decision) -> bool:
    if invariant == "before==after":
        return before == after
    if invariant == "before==ALLOW and after==DENY":
        return before == "ALLOW" and after == "DENY"
    if invariant == "before==DENY and after==DENY":
        return before == "DENY" and after == "DENY"
    if invariant == "before==ALLOW implies after==ALLOW":
        return before != "ALLOW" or after == "ALLOW"
    raise ValueError(f"unknown invariant: {invariant}")


@dataclass(frozen=True)
class ReplayRow:
    failure_id: str
    adapter_id: str
    relation_id: str
    source_id: str
    expected_invariant: str
    recorded_before: str
    recorded_after: str
    replay_before: str
    replay_after: str
    expected_holds_on_replay: bool
    recorded_matches_replay: bool
    status: str
    replay_digest: str

    def as_csv(self) -> dict[str, str]:
        return {
            "failure_id": self.failure_id,
            "adapter_id": self.adapter_id,
            "relation_id": self.relation_id,
            "source_id": self.source_id,
            "expected_invariant": self.expected_invariant,
            "recorded_before": self.recorded_before,
            "recorded_after": self.recorded_after,
            "replay_before": self.replay_before,
            "replay_after": self.replay_after,
            "expected_holds_on_replay": str(self.expected_holds_on_replay).lower(),
            "recorded_matches_replay": str(self.recorded_matches_replay).lower(),
            "status": self.status,
            "replay_digest": self.replay_digest,
        }


def replay_rows(root: Path) -> list[ReplayRow]:
    path = root / "results" / "counterexamples.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    out: list[ReplayRow] = []
    for row in rows:
        before_policy = row["minimal_before_policy"]
        after_policy = row["minimal_after_policy"]
        before_req = row.get("before_request", row.get("request", {}))
        after_req = row.get("after_request", row.get("request", {}))
        before = mutant_decision(row["adapter_id"], before_policy, before_req)
        after = mutant_decision(row["adapter_id"], after_policy, after_req)
        inv_ok = invariant_holds(row["expected_invariant"], before, after)
        recorded_before = row.get("observed_before_decision", "")
        recorded_after = row.get("observed_after_decision", "")
        recorded_matches = (recorded_before == before and recorded_after == after)
        # A counterexample row is valid only when replayed observations match
        # the recorded observations and violate the expected law invariant.
        status = "PASS" if recorded_matches and not inv_ok else "FAIL"
        digest = sha256_text(stable_json([
            row.get("failure_id"), row.get("adapter_id"), row.get("relation_id"),
            row.get("source_id"), before, after, row.get("expected_invariant"), status
        ]))
        out.append(ReplayRow(
            str(row.get("failure_id", "")), str(row.get("adapter_id", "")),
            str(row.get("relation_id", "")), str(row.get("source_id", "")),
            str(row.get("expected_invariant", "")), str(recorded_before), str(recorded_after),
            before, after, inv_ok, recorded_matches, status, digest
        ))
    return sorted(out, key=lambda r: r.failure_id)


def write_semantic_counterexample_replay(root: Path) -> dict[str, Any]:
    rows = replay_rows(root)
    result_dir = root / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    csv_path = result_dir / "semantic_counterexample_replay.csv"
    fields = [
        "failure_id", "adapter_id", "relation_id", "source_id", "expected_invariant",
        "recorded_before", "recorded_after", "replay_before", "replay_after",
        "expected_holds_on_replay", "recorded_matches_replay", "status", "replay_digest"
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_csv())
    failures = [row.as_csv() for row in rows if row.status != "PASS"]
    by_adapter: dict[str, int] = {}
    by_relation: dict[str, int] = {}
    for row in rows:
        by_adapter[row.adapter_id] = by_adapter.get(row.adapter_id, 0) + 1
        by_relation[row.relation_id] = by_relation.get(row.relation_id, 0) + 1
    report = {
        "status": "PASS" if not failures else "FAIL",
        "counterexamples_semantically_replayed": len(rows),
        "semantic_replay_failures": len(failures),
        "adapters": dict(sorted(by_adapter.items())),
        "relations": dict(sorted(by_relation.items())),
        "digest": sha256_text(stable_json(sorted(row.replay_digest for row in rows))),
        "csv": "results/semantic_counterexample_replay.csv",
        "errors": failures[:20],
    }
    (result_dir / "semantic_counterexample_replay.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report
