# LatticeGuard Locked Study Protocol

This file records the pre-result experimental contract for the LatticeGuard artifact. It fixes the research questions, relation catalog, adapter targets, corpus rules, denominator policy, baselines, ablations, robustness checks, stopping condition, and amendment policy. Later changes must be recorded in `protocol_amendments.csv` before the changed run is used for paper claims.

## Research questions

RQ1. Which access-control laws are executable as metamorphic obligations with explicit applicability predicates over the frozen subject corpus and adapter fragments?

RQ2. Do the obligations detect seeded evaluator semantic drift without a hand-written golden decision oracle?

RQ3. How often would invalid transformations be admitted if applicability and rejection discipline were disabled?

RQ4. Is the deterministic artifact replayable across declared scalability axes and Python hash seeds?

## Denominator policy

Only rows with `applicability_status=APPLICABLE_EVALUATED` enter the primary pass/fail denominator. Rows marked `REJECTED_NOT_COUNTED`, `UNSUPPORTED_NOT_COUNTED`, `ERROR_RECORDED`, or `TIMEOUT_RECORDED` must be reported but cannot increase the pass count. The verifier enforces this rule.

## Adapter targets

The primary targets are OPA/Rego CLI, Casbin via PyCasbin, and Cedar via cedarpy. The run must report exactly which adapters executed. The current locked packet counts all three targets: Casbin, Cedar, and OPA/Rego. OPA/Rego may enter the denominator only after its executable passes the SHA-256 pinning contract; otherwise it must be excluded before any OPA result is observed and the objective reason must be recorded in `results/adapter_exclusions.csv`. Claim traceability is closed by `results/claim_traceability_matrix.csv` and `results/claim_verification.json`; paper-visible quantitative claims must map to those ledgers.

OPA/Rego implementation boundary. The OPA adapter is a hash-gated external CLI adapter over the same normalized law object used by the other replay paths. For the locked hierarchy stress cases, the artifact precomputes each principal's transitive role closure with `role_closure()` and provides it to Rego as `data.reachable_roles`; Rego then evaluates allow/deny by checking reachable role membership, action, resource, and deny-overrides. This is counted as OPA execution for the normalized fragment, not as a claim that OPA natively computed arbitrary recursive RBAC hierarchies. The closure function is therefore part of the trusted semantic core and must be covered by unit tests, bounded model checks, and mechanized law-kernel evidence before OPA rows can support claims.

## Corpus rules

The public stratum consists of executable slices transcribed from official public examples or documentation plus native-format public fixture imports. The generated stratum consists of deterministic canonical law probes generated from the frozen relation catalog. Every local subject fixture and every native raw fixture must have a source URL or artifact origin, license note, artifact-relative path, and SHA-256 in `source_manifest.csv`.

The corpus must not be described as a broad upstream benchmark unless complete upstream suites are actually imported, versioned, and evaluated.

The locked 120-source corpus must be reported as stratified evidence: 6 documentation-derived slices, 7 upstream example slices, 10 native canonical fixture slices, 96 deterministic semantic stress witnesses, and 1 generated canonical law probe. Stress witnesses are generated from the frozen relation catalog to exercise relation interactions and denominator boundaries; they are not independent upstream benchmarks. No source, relation candidate, rejected transformation, unsupported row, or seeded control may be removed after observing adapter outcomes merely to improve the pass rate. Any future corpus expansion must be recorded as a protocol amendment before the changed run is used for claims.

## Relation catalog

The frozen relation IDs are: `DD`, `DO`, `PA`, `DA`, `IE`, `ID`, `HC`, `HR`, `SR`, `RO`, `AR`, and `SM`. Each relation must have an executable applicability predicate, expected invariant/order, invalid-transformation rejection rule, unsupported-feature accounting, and minimization criterion. Candidate constructors may propose transformations but must not be trusted to decide denominator status; `predicate_evaluations.csv` and `soundness_checks.csv` are required evidence. The machine-readable relation contracts appear in `results/relation_contracts.csv`.

## Baselines and controls

The artifact must include: cross-adapter differential-only comparison, no-applicability-gate ablation, random-valid-perturbation control, seeded-mutant positive controls, public-only and generated-only subject ablations, removal of counterexample minimization, removal of invalid-transformation rejection, removal of hierarchy/refactoring relation families, and single-relation ablations. Seeded mutants are positive controls only and must not be reported as real adapter bugs.

Adapter/reference agreement is a consistency gate, not an oracle-validity proof. It verifies that enabled adapters and the normalized reference evaluator agree on admitted rows and helps expose adapter, normalization, or fixture-generation mistakes. Correctness of the metamorphic oracle must be justified independently by relation contracts, executable applicability predicates, invalid-transformation rejection, reference-soundness checks, theorem/proof-obligation ledgers, bounded finite model checking, mechanized law-kernel replay, and seeded-control replay.

The locked run may report zero observed real adapter-law violations only with the explicit qualifier that no pre-existing implementation defects were found in the counted Casbin, Cedar, and OPA adapters. Seeded mutants and minimized counterexamples provide ground-truth controls for known semantic drift; they do not establish that the artifact discovered organic bugs in those mature adapters.

## Scalability and robustness

Scalability rows exercise deterministic plumbing over rule count, principal/resource/action count, hierarchy depth, hierarchy branching factor, request-count budget, relation families enabled, and adapters enabled. Runtime and memory fields are normalized and cannot support performance claims. Robustness replay compares deterministic output hashes under Python hash seeds 0, 1, and 42.

## Failure handling

Adapter exceptions, unsupported features, and timeouts are evidence, not reasons to silently drop rows. The row must be recorded with a terminal status and excluded from the pass denominator unless it is an applicable evaluated pass/fail row.

## Stopping condition

The run stops only after every generated candidate for the frozen corpus, relation catalog, seeds, and adapter pins has a terminal status. The experiment must not continue generating candidates because more failures are desired, and it must not stop early because results look favorable.

## Claim verification

Paper-visible numeric claims must be derived from `results/claim_manifest.json` and `results/paper_claims.csv`, surfaced through `paper/claim_macros.tex`, mirrored in `results/claim_macros_snapshot.tex` for artifact-standalone replay, and checked by `scripts/verify_full_claims.py`.

## Amendment policy

Any change to research questions, metrics, denominator rules, corpus rules, adapter pins, baselines, controls, ablations, robustness checks, scalability axes, failure policy, or stopping condition must be recorded in `protocol_amendments.csv` before the changed run is used for paper-visible claims.


## Protocol hardening checks

The optimized artifact adds two evidence streams that do not change the primary adapter pass denominator. First, bounded core model checking enumerates a finite deny-overrides RBAC algebra over the locked enumeration envelope (the 3-role / 2-user / 1-action / 1-resource / rules<=2 search used by the checker) and checks every relation predicate/invariant family against the reference evaluator. These rows are reported in `results/model_check_cases.csv` and summarized in `results/model_check_summary.json`; failures are P0 evidence-integrity failures. Second, native raw-fixture self-tests execute Casbin and Cedar native fixture files before normalization and report `results/native_selftest_results.csv`; failures are P0 adapter-provenance failures. Neither evidence stream may be used to inflate applicable adapter passes.

## Evidence boundary notes

The baseline families above are intentionally asymmetric. `RANDOM_VALID_PERTURB` and `PROPERTY_GENERATOR_NO_REJECTION` are denominator-safety controls, `CROSS_ADAPTER_DIFFERENTIAL_ONLY` is an adapter comparability control, and `SINGLE_RELATION` is a relation-isolation control. None of them substitutes for the full 12-relation oracle.

`model_check_summary.json` is bounded exact evidence: 74,024 cases, 0 failures, 6,336 enumerated policies, and 12 covered relation families. That bounded model-check scope is separate from the 5,040 semantic counterexamples in `counterexamples.json`; the former checks the locked finite envelope, while the latter records replayable failure witnesses from the seeded/differential corpus. It supports the consistency of the frozen relation catalog inside the finite search bound, not a universal theorem.

`scalability.csv` is a trend/boundary ledger only. Its runtime and memory fields are normalized for engineering comparison and must not be read as a performance claim.

Quality, delivery, conference-conformance, and scorecard gates are meta-evidence. They close stale-claim, packaging, traceability, dependency, residue, and reproducibility risks, but they must not be cited as independent scientific accuracy or novelty results. Scientific claims must be supported by the primary obligations, adapter/reference agreement, bounded model checking, mechanized law-kernel replay, native fixture selftests, seeded controls, and explicitly scoped error analysis.
