from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .law_algebra import CorePolicy, Request, Rule, decide, matching_rules, policy_digest_material, reachable_roles

RELATIONS = ("DD", "DO", "PA", "DA", "IE", "ID", "HC", "HR", "SR", "RO", "AR", "SM")
ACTIONS = ("read", "write")
RESOURCES = ("repo:public", "repo:reports")
PRINCIPALS = ("alice", "bob", "mallory")


def stable_json(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(data: object) -> str:
    return hashlib.sha256(stable_json(data).encode("utf-8")).hexdigest()


def req_dict(req: Request) -> dict[str, str]:
    return {"principal": req.principal, "action": req.action, "resource": req.resource}


def policy_dict(policy: CorePolicy) -> dict[str, object]:
    return {
        "assignments": {k: sorted(v) for k, v in sorted(policy.assignments.items())},
        "inherits": {k: sorted(v) for k, v in sorted(policy.inherits.items())},
        "rules": [r.__dict__ for r in policy.rules],
    }


def policy_hash(policy: CorePolicy) -> str:
    return digest(policy_digest_material(policy))


def request_hash(req: Request) -> str:
    return digest(req_dict(req))


def base_policy(principal: str, role: str, action: str, resource: str, *, include_deny: bool = False) -> CorePolicy:
    rules = [Rule("allow", role, action, resource)]
    assignments: dict[str, frozenset[str]] = {
        principal: frozenset({role}),
        "mallory": frozenset({"suspended"}),
    }
    inherits: dict[str, frozenset[str]] = {
        "viewer": frozenset(),
        "editor": frozenset({"viewer"}),
        "owner": frozenset({"editor"}),
        "suspended": frozenset(),
        "shadow": frozenset(),
        "child": frozenset(),
        "off_slice": frozenset(),
    }
    if include_deny:
        rules.append(Rule("deny", "suspended", action, resource))
    return CorePolicy(assignments=assignments, inherits=inherits, rules=tuple(rules))


def with_rule(policy: CorePolicy, rule: Rule) -> CorePolicy:
    return replace(policy, rules=policy.rules + (rule,))


def without_rule(policy: CorePolicy, rule: Rule) -> CorePolicy:
    removed = False
    new_rules: list[Rule] = []
    for r in policy.rules:
        if not removed and r == rule:
            removed = True
            continue
        new_rules.append(r)
    return replace(policy, rules=tuple(new_rules))


def with_assignment(policy: CorePolicy, principal: str, roles: Iterable[str]) -> CorePolicy:
    assignments = {k: frozenset(v) for k, v in policy.assignments.items()}
    assignments[principal] = frozenset(roles)
    return replace(policy, assignments=assignments)


def with_inherits(policy: CorePolicy, role: str, parents: Iterable[str]) -> CorePolicy:
    inherits = {k: frozenset(v) for k, v in policy.inherits.items()}
    inherits[role] = frozenset(parents)
    return replace(policy, inherits=inherits)


def rename_role(policy: CorePolicy, old: str, new: str) -> CorePolicy:
    assignments = {p: frozenset(new if r == old else r for r in roles) for p, roles in policy.assignments.items()}
    inherits: dict[str, frozenset[str]] = {}
    for role, parents in policy.inherits.items():
        role2 = new if role == old else role
        inherits[role2] = frozenset(new if p == old else p for p in parents)
    rules = tuple(Rule(r.effect, new if r.role == old else r.role, r.action, r.resource) for r in policy.rules)
    return CorePolicy(assignments, inherits, rules)


def invariant_holds(expected: str, before: str, after: str) -> bool:
    if expected == "before==after":
        return before == after
    if expected == "after==DENY":
        return after == "DENY"
    if expected == "before_DENY_implies_after_DENY":
        return before != "DENY" or after == "DENY"
    if expected == "before_ALLOW_implies_after_ALLOW":
        return before != "ALLOW" or after == "ALLOW"
    raise ValueError(f"unknown invariant: {expected}")


def _row(case_no: int, relation_id: str, theorem_name: str, before: CorePolicy, after: CorePolicy, before_req: Request, after_req: Request, expected: str, predicate: str, proof_obligation: str) -> dict[str, str]:
    before_decision = decide(before, before_req)
    after_decision = decide(after, after_req)
    status = "PASS" if invariant_holds(expected, before_decision, after_decision) else "FAIL"
    witness = {
        "relation_id": relation_id,
        "before_matching": [r.__dict__ for r in matching_rules(before, before_req)],
        "after_matching": [r.__dict__ for r in matching_rules(after, after_req)],
        "before_roles": sorted(reachable_roles(before, before_req.principal)),
        "after_roles": sorted(reachable_roles(after, after_req.principal)),
        "predicate": predicate,
        "expected": expected,
    }
    return {
        "case_id": f"MK-{relation_id}-{case_no:05d}",
        "relation_id": relation_id,
        "theorem_name": theorem_name,
        "law_predicate": predicate,
        "proof_obligation": proof_obligation,
        "before_policy_hash": policy_hash(before),
        "after_policy_hash": policy_hash(after),
        "before_request_hash": request_hash(before_req),
        "after_request_hash": request_hash(after_req),
        "before_decision": before_decision,
        "after_decision": after_decision,
        "expected_invariant": expected,
        "witness_digest": digest(witness),
        "status": status,
    }


def generate_kernel_rows() -> list[dict[str, str]]:
    """Replay all 12 law families in a small exact semantics kernel.

    The kernel deliberately does not call Casbin or Cedar.  It checks the
    algebraic side conditions used by the paper against a compact deny-overrides
    authorization semantics so the proof evidence is independent of adapter
    behaviour and independent of the large primary obligation ledger.
    """
    rows: list[dict[str, str]] = []
    case_no = 0
    roles = ("viewer", "editor", "owner")
    for principal in PRINCIPALS:
        for role in roles:
            for action in ACTIONS:
                for resource in RESOURCES:
                    req = Request(principal, action, resource)
                    base = base_policy(principal, role, action, resource, include_deny=True)
                    # DD: no reachable matching rule forces default deny.
                    empty = replace(base, rules=tuple(r for r in base.rules if not (r.action == action and r.resource == resource)))
                    case_no += 1
                    rows.append(_row(case_no, "DD", "default_deny_empty_slice", empty, empty, req, req, "after==DENY", "no reachable matching allow or deny", "matching_rules(P,q)=empty => Eval(P,q)=DENY"))
                    # DO: adding a matching deny dominates a previously matching allow.
                    allow_only = replace(base, rules=(Rule("allow", role, action, resource),))
                    with_deny = with_rule(allow_only, Rule("deny", role, action, resource))
                    case_no += 1
                    rows.append(_row(case_no, "DO", "deny_dominates_matching_allow", allow_only, with_deny, req, req, "after==DENY", "same request slice gains a reachable matching deny", "exists matching deny in P' => Eval(P',q)=DENY"))
                    # PA: adding roles preserves ALLOW only if no newly reachable deny matches.
                    before = with_assignment(base, principal, {role})
                    after = with_assignment(base, principal, {role, "shadow"})
                    case_no += 1
                    rows.append(_row(case_no, "PA", "deny_aware_principal_monotonicity", before, after, req, req, "before_ALLOW_implies_after_ALLOW", "role closure grows and new roles carry no matching deny", "ALLOW(P,q) and no new matching deny => ALLOW(P',q')"))
                    # DA: deny witness remains reachable after principal substitution.
                    deny_policy = with_assignment(base, principal, {role, "suspended"})
                    deny_after = with_assignment(deny_policy, principal, {role, "suspended", "shadow"})
                    case_no += 1
                    rows.append(_row(case_no, "DA", "deny_witness_preservation", deny_policy, deny_after, req, req, "before_DENY_implies_after_DENY", "original matching deny remains reachable", "DENY(P,q) by surviving deny witness => DENY(P',q')"))
                    # IE: off-slice extension leaves matching slice unchanged.
                    off = with_rule(base, Rule("allow", "off_slice", "admin", "repo:archive"))
                    off = with_assignment(off, "outsider", {"off_slice"})
                    case_no += 1
                    rows.append(_row(case_no, "IE", "irrelevant_extension_slice_preservation", base, off, req, req, "before==after", "extension is outside principal/action/resource slice", "unchanged matching slice => equal decision"))
                    # ID: duplicating an identical rule is idempotent under deny-overrides.
                    duplicate = with_rule(base, base.rules[0])
                    case_no += 1
                    rows.append(_row(case_no, "ID", "identical_rule_idempotence", base, duplicate, req, req, "before==after", "added rule is semantically identical", "duplicating a rule does not change existence of matching allow/deny"))
                    # HC: adding an already-implied hierarchy edge leaves closure unchanged.
                    hbase = with_inherits(with_inherits(base, "owner", {"editor"}), "editor", {"viewer"})
                    hbase = with_assignment(hbase, principal, {"owner"})
                    hafter = with_inherits(hbase, "owner", {"editor", "viewer"})
                    case_no += 1
                    rows.append(_row(case_no, "HC", "transitive_hierarchy_closure_edge", hbase, hafter, req, req, "before==after", "inserted edge is already in transitive closure", "closure-equivalent hierarchy => equal decision"))
                    # HR: refactor assignment through a child role that inherits the old role.
                    hr_before = with_assignment(base, principal, {role})
                    hr_after = with_inherits(base, "child", {role})
                    hr_after = with_assignment(hr_after, principal, {"child"})
                    case_no += 1
                    rows.append(_row(case_no, "HR", "hierarchy_refactoring_child_role", hr_before, hr_after, req, req, "before==after", "child role inherits exactly the old request-relevant role", "closure-preserving assignment refactor => equal decision"))
                    # SR: remove an allow shadowed by a matching deny and decision remains DENY.
                    sr_before = with_assignment(with_rule(allow_only, Rule("deny", role, action, resource)), principal, {role})
                    sr_after = without_rule(sr_before, Rule("allow", role, action, resource))
                    case_no += 1
                    rows.append(_row(case_no, "SR", "shadowed_allow_removal", sr_before, sr_after, req, req, "before==after", "removed allow is dominated by surviving matching deny", "dominant deny makes shadowed allow observationally irrelevant"))
                    # RO: unordered deny-overrides semantics is invariant to rule order.
                    ro_before = replace(base, rules=(Rule("allow", role, action, resource), Rule("deny", "suspended", action, resource), Rule("allow", "off_slice", action, resource)))
                    ro_after = replace(base, rules=tuple(reversed(ro_before.rules)))
                    case_no += 1
                    rows.append(_row(case_no, "RO", "unordered_rule_permutation", ro_before, ro_after, req, req, "before==after", "fragment has no priority/first-match/last-match operator", "permutation preserves matching allow/deny sets"))
                    # AR: off-slice alpha renaming does not touch the requested closure.
                    ar_before = with_assignment(with_rule(base, Rule("allow", "off_slice", action, resource)), "outsider", {"off_slice"})
                    ar_after = rename_role(ar_before, "off_slice", "renamed_off_slice")
                    case_no += 1
                    rows.append(_row(case_no, "AR", "off_slice_alpha_renaming", ar_before, ar_after, req, req, "before==after", "injective rename leaves requested principal/action/resource slice untouched", "renaming unreachable atoms preserves the requested decision"))
                    # SM: split/merge preserves coverage of the matched target slice.
                    sm_before = replace(base, rules=(Rule("allow", role, action, resource), Rule("allow", role, action, "repo:reports")))
                    sm_after = replace(base, rules=(Rule("allow", role, action, resource), Rule("allow", role, action, "repo:reports"), Rule("allow", "off_slice", action, "repo:archive")))
                    case_no += 1
                    rows.append(_row(case_no, "SM", "scope_split_merge_target_equivalence", sm_before, sm_after, req, req, "before==after", "replacement covers exactly the same matched target slice", "target-slice equivalent scope split/merge preserves decision"))
    rows.sort(key=lambda r: (r["relation_id"], r["case_id"]))
    return rows


FIELDNAMES = [
    "case_id", "relation_id", "theorem_name", "law_predicate", "proof_obligation",
    "before_policy_hash", "after_policy_hash", "before_request_hash", "after_request_hash",
    "before_decision", "after_decision", "expected_invariant", "witness_digest", "status",
]


def write_csv(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


def build_summary(rows: Sequence[Mapping[str, str]]) -> dict[str, object]:
    counts = Counter(r["relation_id"] for r in rows)
    failures = [r["case_id"] for r in rows if r.get("status") != "PASS"]
    theorem_names = sorted({r["theorem_name"] for r in rows})
    return {
        "certificate_kind": "independent_mechanized_law_kernel_replay",
        "status": "PASS" if not failures and set(counts) == set(RELATIONS) and min(counts.values() or [0]) >= 12 else "FAIL",
        "relations_covered": len(counts),
        "relations_expected": len(RELATIONS),
        "cases_checked": len(rows),
        "failures": len(failures),
        "failure_case_ids": failures[:20],
        "cases_by_relation": dict(sorted(counts.items())),
        "theorems_checked": len(theorem_names),
        "theorem_names_digest": digest(theorem_names),
        "row_digest": digest(list(rows)),
        "semantics": "finite exact deny-overrides/default-deny core independent of external adapters",
    }


def write_mechanized_law_kernel(root: Path) -> dict[str, object]:
    results = root / "results"
    rows = generate_kernel_rows()
    write_csv(results / "mechanized_law_kernel.csv", rows)
    summary = build_summary(rows)
    (results / "mechanized_law_kernel.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
