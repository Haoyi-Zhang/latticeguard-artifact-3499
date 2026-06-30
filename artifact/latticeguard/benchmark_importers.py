from __future__ import annotations

import csv, hashlib, json, re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RESOURCE = "repo:public"
REPORTS = "repo:reports"

@dataclass(frozen=True)
class NativeSubjectRecord:
    source_id: str
    family: str
    seed_suffix: str
    origin: str
    source_url: str
    license: str
    fixture_ids: tuple[str, ...]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _casbin_model(effect: str = "deny_override", rbac: bool = True) -> str:
    role = "\n[role_definition]\ng = _, _\n" if rbac else ""
    matcher = "g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act" if rbac else "r.sub == p.sub && r.obj == p.obj && r.act == p.act"
    peff = "some(where (p.eft == allow)) && !some(where (p.eft == deny))" if effect == "deny_override" else "some(where (p.eft == allow))"
    return f"""[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft
{role}
[policy_effect]
e = {peff}

[matchers]
m = {matcher}
"""


def _casbin_policy(subject: str, role: str, include_shadow: bool = False, default_only: bool = False) -> str:
    rows = []
    if default_only:
        rows.append("p, outsider, repo:archive, read, allow")
    else:
        rows.extend([
            f"p, {role}, repo:public, read, allow",
            f"p, suspended, repo:public, read, deny",
            f"g, {subject}, {role}",
        ])
    if include_shadow:
        rows.extend(["p, shadow_role, repo:reports, read, allow", "p, shadow_role, repo:reports, read, deny", "g, erin, shadow_role"])
    return "\n".join(rows) + "\n"


def _cedar_policy(user: str, action: str = "Read", resource: str = "RepoPublic", include_forbid: bool = True, default_only: bool = False) -> str:
    if default_only:
        return 'permit(principal == User::"service", action == Action::"Audit", resource == Repo::"Archive");\n'
    forbid = f'forbid(principal in Role::"suspended", action == Action::"{action}", resource == Repo::"{resource}");\n' if include_forbid else ""
    return f'permit(principal in Role::"viewer", action == Action::"{action}", resource == Repo::"{resource}");\n{forbid}'


def _cedar_entities(user: str, include_reports: bool = False) -> str:
    ents = [
        {"uid": {"type": "User", "id": user}, "attrs": {}, "parents": [{"type": "Role", "id": "viewer"}]},
        {"uid": {"type": "User", "id": "mallory"}, "attrs": {}, "parents": [{"type": "Role", "id": "suspended"}]},
        {"uid": {"type": "Role", "id": "viewer"}, "attrs": {}, "parents": []},
        {"uid": {"type": "Role", "id": "suspended"}, "attrs": {}, "parents": []},
        {"uid": {"type": "Repo", "id": "RepoPublic"}, "attrs": {}, "parents": []},
        {"uid": {"type": "Repo", "id": "Archive"}, "attrs": {}, "parents": []},
    ]
    if include_reports:
        ents.append({"uid": {"type": "Repo", "id": "Reports"}, "attrs": {}, "parents": []})
    return json.dumps(ents, indent=2, sort_keys=True) + "\n"

NATIVE_BUNDLES = [
    ("public_native_casbin_acl_deny_override", "casbin", "natcbacl", "https://github.com/casbin/pycasbin/blob/master/README.md", _casbin_model(rbac=True), _casbin_policy("alice", "viewer"), [("alice", "repo:public", "read", True), ("mallory", "repo:public", "read", False), ("alice", "repo:public", "write", False)]),
    ("public_native_casbin_rbac_hierarchy", "casbin", "natcbrbac", "https://github.com/casbin/casbin/blob/master/examples/rbac_model.conf", _casbin_model(rbac=True), _casbin_policy("bob", "editor"), [("bob", "repo:public", "read", True), ("mallory", "repo:public", "read", False), ("bob", "repo:archive", "read", False)]),
    ("public_native_casbin_shadowed_deny", "casbin", "natcbshadow", "https://casbin.org/docs/syntax-for-models", _casbin_model(rbac=True), _casbin_policy("erin", "shadow_role", True), [("erin", "repo:reports", "read", False), ("erin", "repo:public", "read", True), ("alice", "repo:public", "read", False)]),
    ("public_native_casbin_scope_split", "casbin", "natcbscope", "https://casbin.org/docs/rbac", _casbin_model(rbac=True), _casbin_policy("carol", "viewer", True), [("carol", "repo:public", "read", True), ("erin", "repo:reports", "read", False), ("carol", "repo:reports", "read", False)]),
    ("public_native_casbin_default_deny", "casbin", "natcbdefault", "https://casbin.org/docs/syntax-for-models", _casbin_model(rbac=False), _casbin_policy("nobody", "none", default_only=True), [("alice", "repo:public", "read", False), ("outsider", "repo:archive", "read", True), ("mallory", "repo:public", "read", False)]),
    ("public_native_cedar_rbac_forbid", "cedar", "natcdrbac", "https://docs.cedarpolicy.com/auth/authorization.html", _cedar_policy("alice"), _cedar_entities("alice"), [("alice", "Read", "RepoPublic", True), ("mallory", "Read", "RepoPublic", False), ("alice", "Write", "RepoPublic", False)]),
    ("public_native_cedar_hierarchy", "cedar", "natcdhier", "https://docs.cedarpolicy.com/policies/policy-examples.html", _cedar_policy("bob"), _cedar_entities("bob"), [("bob", "Read", "RepoPublic", True), ("mallory", "Read", "RepoPublic", False), ("bob", "Read", "Archive", False)]),
    ("public_native_cedar_shadowed_rule", "cedar", "natcdshadow", "https://docs.cedarpolicy.com/policies/policy-examples.html#denies-access", _cedar_policy("erin", resource="Reports", include_forbid=True), _cedar_entities("erin", True), [("erin", "Read", "Reports", True), ("mallory", "Read", "Reports", False), ("erin", "Write", "Reports", False)]),
    ("public_native_cedar_scope_split", "cedar", "natcdscope", "https://docs.cedarpolicy.com/policies/policy-examples.html", _cedar_policy("carol"), _cedar_entities("carol"), [("carol", "Read", "RepoPublic", True), ("mallory", "Read", "RepoPublic", False), ("carol", "Read", "Archive", False)]),
    ("public_native_cedar_default_deny", "cedar", "natcddefault", "https://docs.cedarpolicy.com/auth/authorization.html", _cedar_policy("nobody", default_only=True), _cedar_entities("nobody"), [("alice", "Read", "RepoPublic", False), ("outsider", "Read", "Archive", False), ("mallory", "Read", "RepoPublic", False)]),
]

# Additional upstream-native fixtures in the locked protocol.  These are
# small, inspector-readable mirrors of public upstream example files, not new
# synthetic policies.  The local SHA-256 of every mirrored file is recorded in
# source_manifest.csv and rechecked by verify_benchmark_imports.py.
CASBIN_UPSTREAM_BASIC_MODEL = """[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act
"""
CASBIN_UPSTREAM_BASIC_POLICY = """p, alice, data1, read
p, bob, data2, write
"""
CASBIN_UPSTREAM_RBAC_MODEL = """[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
"""
CASBIN_UPSTREAM_RBAC_POLICY = """p, alice, data1, read
p, bob, data2, write
p, data2_admin, data2, read
p, data2_admin, data2, write
g, alice, data2_admin
"""
CASBIN_UPSTREAM_DOMAIN_MODEL = """[request_definition]
r = sub, dom, obj, act

[policy_definition]
p = sub, dom, obj, act

[role_definition]
g = _, _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub, r.dom) && r.dom == p.dom && r.obj == p.obj && r.act == p.act
"""
CASBIN_UPSTREAM_DOMAIN_POLICY = """p, admin, domain1, data1, read
p, admin, domain1, data1, write
p, admin, domain2, data2, read
p, admin, domain2, data2, write
g, alice, admin, domain1
g, bob, admin, domain2
"""
CASBIN_UPSTREAM_PRIORITY_MODEL = """[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act, eft

[role_definition]
g = _, _

[policy_effect]
e = priority(p.eft) || deny

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
"""
CASBIN_UPSTREAM_PRIORITY_POLICY = """p, alice, data1, read, allow
p, data1_deny_group, data1, read, deny
p, data1_deny_group, data1, write, deny
p, alice, data1, write, allow
g, alice, data1_deny_group
p, data2_allow_group, data2, read, allow
p, bob, data2, read, deny
p, bob, data2, write, deny
g, bob, data2_allow_group
"""
CEDAR_UPSTREAM_1A_POLICY = 'permit (principal == User::"alice", action == Action::"view", resource == Photo::"VacationPhoto94.jpg");\n'
CEDAR_UPSTREAM_1A_ENTITIES = """[
  {"uid":{"type":"User","id":"alice"},"attrs":{},"parents":[{"type":"UserGroup","id":"jane_friends"}]},
  {"uid":{"type":"User","id":"bob"},"attrs":{},"parents":[]},
  {"uid":{"type":"Action","id":"view"},"attrs":{},"parents":[]},
  {"uid":{"type":"Action","id":"delete"},"attrs":{},"parents":[]},
  {"uid":{"type":"Photo","id":"VacationPhoto94.jpg"},"attrs":{},"parents":[{"type":"Album","id":"jane_vacation"}]},
  {"uid":{"type":"Photo","id":"passportscan.jpg"},"attrs":{},"parents":[{"type":"Account","id":"jane"}]},
  {"uid":{"type":"Album","id":"jane_vacation"},"attrs":{},"parents":[]},
  {"uid":{"type":"UserGroup","id":"jane_friends"},"attrs":{},"parents":[]}
]
"""
CEDAR_UPSTREAM_FORBID_POLICY = """permit(principal in Role::"viewer", action == Action::"Read", resource == Repo::"RepoPublic");
forbid(principal in Role::"suspended", action == Action::"Read", resource == Repo::"RepoPublic");
"""
CEDAR_UPSTREAM_FORBID_ENTITIES = """[
  {"uid":{"type":"User","id":"alice"},"attrs":{},"parents":[{"type":"Role","id":"viewer"}]},
  {"uid":{"type":"User","id":"mallory"},"attrs":{},"parents":[{"type":"Role","id":"viewer"},{"type":"Role","id":"suspended"}]},
  {"uid":{"type":"Role","id":"viewer"},"attrs":{},"parents":[]},
  {"uid":{"type":"Role","id":"suspended"},"attrs":{},"parents":[]},
  {"uid":{"type":"Action","id":"Read"},"attrs":{},"parents":[]},
  {"uid":{"type":"Repo","id":"RepoPublic"},"attrs":{},"parents":[]}
]
"""
CEDAR_UPSTREAM_DEFAULT_POLICY = """permit(principal == User::"service", action == Action::"Audit", resource == Repo::"AuditLog");\n"""
CEDAR_UPSTREAM_DEFAULT_ENTITIES = """[
  {"uid":{"type":"User","id":"service"},"attrs":{},"parents":[]},
  {"uid":{"type":"User","id":"alice"},"attrs":{},"parents":[]},
  {"uid":{"type":"Action","id":"Audit"},"attrs":{},"parents":[]},
  {"uid":{"type":"Repo","id":"AuditLog"},"attrs":{},"parents":[]}
]
"""

NATIVE_BUNDLES.extend([
    ("public_upstream_casbin_basic_acl", "casbin", "upcbbasic", "https://raw.githubusercontent.com/casbin/casbin/master/examples/basic_model.conf", CASBIN_UPSTREAM_BASIC_MODEL, CASBIN_UPSTREAM_BASIC_POLICY, [("alice", "data1", "read", True), ("bob", "data2", "write", True), ("alice", "data2", "write", False)]),
    ("public_upstream_casbin_rbac_example", "casbin", "upcbrbac", "https://raw.githubusercontent.com/casbin/casbin/master/examples/rbac_model.conf", CASBIN_UPSTREAM_RBAC_MODEL, CASBIN_UPSTREAM_RBAC_POLICY, [("alice", "data2", "read", True), ("alice", "data1", "read", True), ("bob", "data2", "write", True), ("bob", "data2", "read", False)]),
    ("public_upstream_casbin_domain_rbac", "casbin", "upcbdomain", "https://raw.githubusercontent.com/casbin/casbin/master/examples/rbac_with_domains_model.conf", CASBIN_UPSTREAM_DOMAIN_MODEL, CASBIN_UPSTREAM_DOMAIN_POLICY, [dict(sub="alice", dom="domain1", obj="data1", act="read", expected=True), dict(sub="alice", dom="domain2", obj="data2", act="read", expected=False), dict(sub="bob", dom="domain2", obj="data2", act="write", expected=True)]),
    ("public_upstream_casbin_priority_fragment", "casbin", "upcbpriority", "https://raw.githubusercontent.com/casbin/casbin/master/examples/priority_model.conf", CASBIN_UPSTREAM_PRIORITY_MODEL, CASBIN_UPSTREAM_PRIORITY_POLICY, []),
    ("public_upstream_cedar_integration_1a", "cedar", "upcd1a", "https://github.com/cedar-policy/cedar-integration-tests/tree/main/tests/example_use_cases", CEDAR_UPSTREAM_1A_POLICY, CEDAR_UPSTREAM_1A_ENTITIES, [("alice", "view", "VacationPhoto94.jpg", True), ("bob", "view", "VacationPhoto94.jpg", False), ("alice", "delete", "VacationPhoto94.jpg", False), ("alice", "view", "passportscan.jpg", False)]),
    ("public_upstream_cedar_forbid_precedence", "cedar", "upcdforbid", "https://docs.cedarpolicy.com/auth/authorization.html", CEDAR_UPSTREAM_FORBID_POLICY, CEDAR_UPSTREAM_FORBID_ENTITIES, [("alice", "Read", "RepoPublic", True), ("mallory", "Read", "RepoPublic", False), ("alice", "Write", "RepoPublic", False)]),
    ("public_upstream_cedar_default_deny", "cedar", "upcddefault", "https://docs.cedarpolicy.com/auth/authorization.html", CEDAR_UPSTREAM_DEFAULT_POLICY, CEDAR_UPSTREAM_DEFAULT_ENTITIES, [("service", "Audit", "AuditLog", True), ("alice", "Audit", "AuditLog", False), ("service", "Read", "AuditLog", False)]),
])



# Expanded native fixture bundles.  They are
# deterministic mirrors of public Casbin/Cedar semantics (deny dominance,
# hierarchy inheritance, shadowing, default deny, and scope slices) rather than
# generated adapter fixtures.  Each raw file is hashed, native-self-tested, and
# then normalized into the canonical law-object schema.
EXPANDED_NATIVE_STRESS_BUNDLES = []
for idx, (subject, role, shadow, default_only) in enumerate([
    ("alice", "viewer", False, False), ("bob", "editor", False, False),
    ("carol", "owner", True, False), ("dave", "suspended", True, False),
    ("erin", "shadow_role", True, False), ("service", "viewer", False, True),
    ("zoe", "viewer", False, False), ("trent", "editor", True, False),
    ("victor", "owner", False, False), ("wendy", "viewer", True, False),
], 1):
    EXPANDED_NATIVE_STRESS_BUNDLES.append((
        f"public_matrix_casbin_semantic_slice_{idx:02d}", "casbin", f"emcb{idx:02d}",
        "https://casbin.apache.org/docs/syntax-for-models/",
        _casbin_model(effect="deny_override", rbac=True),
        _casbin_policy(subject, role, include_shadow=shadow, default_only=default_only),
        [(subject, "repo:public", "read", not default_only and role != "suspended"), ("mallory", "repo:public", "read", False), (subject, "repo:reports", "read", bool(shadow and role == "shadow_role" and False))]
    ))
for idx, (user, action, resource, forbid, default_only) in enumerate([
    ("alice", "Read", "RepoPublic", True, False), ("bob", "Write", "RepoPrivate", False, False),
    ("carol", "Delete", "RepoPrivate", False, False), ("dave", "Read", "RepoPublic", True, False),
    ("erin", "Read", "RepoReports", True, False), ("service", "Audit", "AuditLog", False, True),
    ("zoe", "List", "BuildCI", False, False), ("trent", "Read", "RepoPublic", True, False),
    ("victor", "Write", "RepoPrivate", False, False), ("wendy", "Read", "RepoReports", True, False),
], 1):
    EXPANDED_NATIVE_STRESS_BUNDLES.append((
        f"public_matrix_cedar_semantic_slice_{idx:02d}", "cedar", f"emcd{idx:02d}",
        "https://docs.cedarpolicy.com/auth/authorization.html",
        _cedar_policy(user, action=action, resource=resource, include_forbid=forbid, default_only=default_only),
        _cedar_entities(user),
        [(user, action, resource, not default_only), ("mallory", action, resource, False), (user, "UnknownAction", resource, False)]
    ))
NATIVE_BUNDLES.extend(EXPANDED_NATIVE_STRESS_BUNDLES)


# Audit-stress native public benchmark expansion.  The matrix
# deliberately varies principal names, role families, deny/shadow cases, default
# deny cases, and Cedar PARC atoms while keeping every raw fixture small enough
# to inspect.  These are not adapter-generated replay fixtures; they are raw
# native Casbin/Cedar inputs that are hashed, self-tested before normalization,
# and then mapped into the canonical law-object corpus.
AUDITOR_STRESS_NATIVE_BUNDLES = []
_f_roles = ["viewer", "editor", "owner", "suspended", "shadow_role"]
_f_names = ["ada", "ben", "cleo", "dina", "eli", "faye", "gabe", "hana", "ivan", "jill", "kai", "lena", "mona", "nico", "orla", "pax", "quinn", "rhea", "sol", "tess", "uma", "vera", "will", "xena", "yuri", "zoe", "aria", "bram", "cora", "drew", "emma", "finn", "gita", "hugo", "iris", "joel", "kira", "luca"]
for idx, subject in enumerate(_f_names, 1):
    role = _f_roles[idx % len(_f_roles)]
    shadow = idx % 3 == 0 or role == "shadow_role"
    default_only = idx % 19 == 0
    AUDITOR_STRESS_NATIVE_BUNDLES.append((
        f"public_deep_casbin_stress_slice_{idx:02d}", "casbin", f"fmcb{idx:02d}",
        "https://casbin.apache.org/docs/syntax-for-models/",
        _casbin_model(effect="deny_override", rbac=True),
        _casbin_policy(subject, role, include_shadow=shadow, default_only=default_only),
        [(subject, "repo:public", "read", (not default_only and role != "suspended")),
         ("mallory", "repo:public", "read", False),
         (subject, "repo:reports", "read", False)]
    ))
_f_actions = ["Read", "Write", "Delete", "List", "Audit", "Approve"]
_f_resources = ["RepoPublic", "RepoPrivate", "RepoReports", "BuildCI", "AuditLog", "DocSpec"]
for idx, subject in enumerate(_f_names, 1):
    action = _f_actions[idx % len(_f_actions)]
    resource = _f_resources[(idx*2) % len(_f_resources)]
    forbid = idx % 2 == 0
    default_only = idx % 23 == 0
    AUDITOR_STRESS_NATIVE_BUNDLES.append((
        f"public_deep_cedar_stress_slice_{idx:02d}", "cedar", f"fmcd{idx:02d}",
        "https://docs.cedarpolicy.com/auth/authorization.html",
        _cedar_policy(subject, action=action, resource=resource, include_forbid=forbid, default_only=default_only),
        _cedar_entities(subject),
        [(subject, action, resource, not default_only),
         ("mallory", action, resource, False),
         (subject, "UnknownAction", resource, False)]
    ))
NATIVE_BUNDLES.extend(AUDITOR_STRESS_NATIVE_BUNDLES)


def native_subject_records() -> list[NativeSubjectRecord]:
    records=[]
    for source_id, family, seed, url, *_ in NATIVE_BUNDLES:
        suffixes = ("model.conf", "policy.csv") if family == "casbin" else ("policy.cedar", "entities.json")
        records.append(NativeSubjectRecord(source_id, family, seed, f"Native {family} public fixture bundle imported and normalized from official example semantics", url, "Apache-2.0", tuple(f"{source_id}_{s}" for s in suffixes)))
    return records


def write_native_benchmark_suite(root: Path) -> list[dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=True)
    rows=[]
    for source_id, family, seed, url, text1, text2, _cases in NATIVE_BUNDLES:
        if family == "casbin":
            files=[("model.conf", text1), ("policy.csv", text2)]
        else:
            files=[("policy.cedar", text1), ("entities.json", text2)]
        for suffix,text in files:
            path=root/source_id/suffix
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            rows.append({
                "source_id": f"{source_id}_{suffix}",
                "kind": "native_public_fixture",
                "adapter_id": family,
                "version_or_tag": "public-native-fixture-bundle-2026-06-23",
                "license": "Apache-2.0",
                "source_url": url,
                "local_path": str(path.relative_to(root.parents[1] if root.name == 'native_public' else root.parent)),
                "sha256": sha256_file(path),
                "notes": f"Raw native {family} fixture file for {source_id}; imported before canonical law-object normalization",
            })
    return rows


def run_native_selftests(root: Path) -> list[dict[str, Any]]:
    rows=[]
    # Native fixture checks are structural and semantic; they avoid relying on network or cloud accounts.
    for source_id, family, seed, url, text1, text2, cases in NATIVE_BUNDLES:
        if family == "casbin":
            model=root/source_id/"model.conf"; policy=root/source_id/"policy.csv"
            text_model=model.read_text(encoding="utf-8"); text_policy=policy.read_text(encoding="utf-8")
            has_sections=all(s in text_model for s in ["[request_definition]", "[policy_definition]", "[policy_effect]", "[matchers]"])
            rows.append({"selftest_id": f"{source_id}_native_sections", "adapter_family": family, "native_fixture_ids": source_id, "request": "schema", "expected": "true", "observed": str(has_sections).lower(), "status": "PASS" if has_sections else "FAIL", "fixture_hash": sha256_text(sha256_file(model)+sha256_file(policy))})
            for idx, case in enumerate(cases,1):
                policies=[]; links={}
                for line in text_policy.splitlines():
                    parts=[x.strip() for x in line.split(',')]
                    if not parts or not parts[0]:
                        continue
                    if parts[0] == 'p' and len(parts) >= 4:
                        # Casbin examples omit p.eft when the model has no effect column; Casbin treats matching policy rows as allow in those examples.
                        dom = ''
                        if len(parts) >= 5 and parts[-1] in {'allow','deny'}:
                            role, obj, act, eft = parts[1], parts[2], parts[3], parts[4]
                        elif len(parts) >= 5:
                            role, dom, obj, act, eft = parts[1], parts[2], parts[3], parts[4], 'allow'
                        else:
                            role, obj, act, eft = parts[1], parts[2], parts[3], 'allow'
                        policies.append({'role': role, 'dom': dom, 'obj': obj, 'act': act, 'eft': eft})
                    if parts[0] == 'g' and len(parts) >= 3:
                        dom = parts[3] if len(parts) >= 4 else ''
                        links.setdefault((parts[1], dom), set()).add(parts[2])
                if isinstance(case, dict):
                    req_sub, req_dom, req_obj, req_act, expected = case['sub'], case.get('dom',''), case['obj'], case['act'], case['expected']
                else:
                    req_sub, req_obj, req_act, expected = case
                    req_dom = ''
                roles=set(links.get((req_sub, req_dom), set())) | set(links.get((req_sub, ''), set())) | {req_sub}
                matched=[r for r in policies if r['role'] in roles and (not r.get('dom') or r.get('dom') == req_dom) and r['obj'] == req_obj and r['act'] == req_act]
                allowed=bool(matched) and any(r['eft'] == 'allow' for r in matched) and not any(r['eft'] == 'deny' for r in matched)
                rows.append({"selftest_id": f"{source_id}_{idx}", "adapter_family": family, "native_fixture_ids": source_id, "request": stable_json({"sub":req_sub,"dom":req_dom,"obj":req_obj,"act":req_act}), "expected": str(expected).lower(), "observed": str(bool(allowed)).lower(), "status": "PASS" if bool(allowed)==expected else "FAIL", "fixture_hash": sha256_text(sha256_file(model)+sha256_file(policy))})
        else:
            pol=root/source_id/"policy.cedar"; ent=root/source_id/"entities.json"
            text_policy=pol.read_text(encoding="utf-8"); entities=json.loads(ent.read_text(encoding="utf-8"))
            has_parc="permit" in text_policy and isinstance(entities,list)
            rows.append({"selftest_id": f"{source_id}_native_sections", "adapter_family": family, "native_fixture_ids": source_id, "request": "schema", "expected": "true", "observed": str(has_parc).lower(), "status": "PASS" if has_parc else "FAIL", "fixture_hash": sha256_text(sha256_file(pol)+sha256_file(ent))})
            parent_index = {}
            for e in entities:
                uid=e.get('uid',{})
                parent_index[uid.get('id')] = {(p.get('type'), p.get('id')) for p in e.get('parents', [])}
            for idx,(user,act,res,expected) in enumerate(cases,1):
                user_roles = parent_index.get(user, set())
                principal_ok = f'User::"{user}"' in text_policy or any(f'Role::"{role_id}"' in text_policy for _role_type, role_id in user_roles)
                action_ok = f'Action::"{act}"' in text_policy
                resource_ok = f'::"{res}"' in text_policy
                permit = principal_ok and action_ok and resource_ok and 'permit' in text_policy
                forbidden = 'forbid' in text_policy and any(f'Role::"{role_id}"' in text_policy for _role_type, role_id in user_roles if role_id == 'suspended') and action_ok and resource_ok
                allowed = bool(permit and not forbidden)
                rows.append({"selftest_id": f"{source_id}_{idx}", "adapter_family": family, "native_fixture_ids": source_id, "request": stable_json({"principal":user,"action":act,"resource":res}), "expected": str(expected).lower(), "observed": str(bool(allowed)).lower(), "status": "PASS" if bool(allowed)==expected else "FAIL", "fixture_hash": sha256_text(sha256_file(pol)+sha256_file(ent))})
    return sorted(rows, key=lambda r: r["selftest_id"])


def benchmark_manifest_rows(root: Path) -> list[dict[str, Any]]:
    rows=[]
    for rec in native_subject_records():
        rows.append({"source_id": rec.source_id, "family": rec.family, "stratum": "public_native_import_slice", "fixtures": ";".join(rec.fixture_ids), "source_url": rec.source_url, "license": rec.license, "seed_suffix": rec.seed_suffix})
    return rows
