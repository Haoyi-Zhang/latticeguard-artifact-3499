# Reproducing the LatticeGuard Artifact

## Requirements

- CPU-only local execution.
- Python 3.13 for the vendored cedarpy wheel included in this packet, or a locally rebuilt cedarpy wheel matching the same pinned version.
- No GPU, cloud account, commercial API, private data, or network access is required for replay.
- Vendored Python packages are included under `vendor_python/`; `requirements.txt` records the pinned package versions used to build the packet.

## System requirements

- Linux x86_64/amd64 with `python3.13`.
- The shipped `cedarpy` bridge is CPython 3.13 native; other Python versions require rebuilding the same pinned package outside this clean packet.
- CPU-only execution; no GPU, cloud account, commercial API, private data, network scan, or hosted service is required.
- Reserve at least 4 GB RAM and 2 GB free disk for full replay outputs.
- Run commands from `artifact/`; scripts use artifact-relative imports and the bundled `vendor_python/` tree.

## Interpretation notes

- The default counted evaluation covers exactly three real adapters: `casbin_py`, `cedar_py`, and hash-gated `opa_rego_cli`.
- OPA/Rego rows are counted only when the pinned executable in `tools/` passes the SHA-256 preflight. If that executable is absent or mismatched, OPA is excluded before any OPA result is observed and the denominator is recomputed.
- The OPA/Rego adapter receives a normalized policy object with `reachable_roles` precomputed by the artifact's `role_closure()` helper. OPA still executes the final allow/deny decision through the pinned CLI, but the hierarchy closure belongs to the artifact's trusted semantic core and is tested separately.
- The 5,040 minimized counterexamples are seeded synthetic controls for replay and minimization; they are not production defects discovered in the counted adapters.
- The adapter/reference agreement ledger is a consistency check over enabled adapters and the normalized reference evaluator. It helps catch adapter or fixture mismatches, but oracle correctness is supported by the relation predicates, reference-soundness ledgers, bounded model checks, and mechanized law-kernel replay rather than by agreement alone.
- The `unsupported` rows are well-formed relation candidates that fall outside the admitted fragment or adapter capability envelope; they are coverage boundaries, not bugs or passes.
- The provenance split distinguishes 23 documentation/upstream/native slices from 96 synthetic stress witnesses and 1 generated law probe, so reviewers should not read the full 120-source set as a pure external-benchmark corpus. The generated/stress subjects are deterministic relation-catalog probes and are not filtered after observing adapter outcomes.

## Minimal replay

```bash
cd artifact
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/run_full_evaluation.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/verify_all.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/finalize_robustness.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/verify_all.py
```

A successful run prints JSON with `"status": "PASS"`. The aggregate verifier checks that:

- exactly the executed primary adapters `casbin_py`, `cedar_py`, and `opa_rego_cli` appear in applicable rows for the current packet;
- OPA/Rego was admitted by the hash-gated preflight before any OPA row entered the denominator;
- rejected and unsupported candidates are not counted as passes;
- every frozen relation ID is covered for both executed adapters;
- bounded core model checking covers all relation families with zero failures;
- theorem/proof-obligation ledgers cover 12 relation theorems and 48 proof obligations;
- the independent mechanized law-kernel replay covers all 12 relation families with zero failures;
- oracle-efficacy, research-quality, protocol-freeze, source-provenance, claim-traceability, manuscript-presentation, open-science-compliance, venue-conformance, and package gate ledgers report PASS;
- native raw Casbin/Cedar fixture self-tests pass before normalization;
- counterexample replay material is embedded in `results/counterexamples.json` and hashes match; see `artifact/README.md` for the control-row interpretation and the model-check vs counterexample scope boundary;
- paper-visible numeric macros match `results/claim_manifest.json` and `results/paper_claims.csv`;
- the SHA-256 ledger matches deterministic output files.

## Optional robustness replay

```bash
cd artifact
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/finalize_robustness.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/finalize_robustness.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/verify_all.py
```

By default this recomputes and validates the authoritative SHA-256 ledger without a costly full rerun. Set `LATTICEGUARD_FULL_ROBUSTNESS=1` to rerun the full evaluation under Python hash seeds 0, 1, and 42.

## Expected primary result scope

The result should contain 15,840 applicable obligations, 15,840 applicable passes, 3,240 rejected invalid transformations, 360 unsupported transformations, 36,960 seeded mutant rows, 5,040 killed seeded rows, 5,040 semantically replayed minimized counterexamples, 74,024 bounded core model-check cases with zero failures, 12 theorem rows, 48 proof obligations, 432 independent mechanized law-kernel replay cases, 9 baseline families, 20 closed research-quality lenses, 11 protocol-freeze checks, 15,840 adapter/reference agreement rows with zero disagreements, 73 reference-integrity entries with zero failures, 120 source-provenance-classified subject sources, 32 traced paper-visible claims, 451 passing native raw-fixture self-tests, 129 aggregate verifier checks, 38 unit tests, 11 closed venue-conformance dimensions, 21 closed reproducibility-risk rows, 6 pinned dependency rows, 14 denominator-integrity checks, 181 compiled Python files, 181 scanned Python files for import-surface closure, and 27 resource/license closure rows, and a package manifest that excludes generated fixture by-products. These are not performance measurements; they report the current hash-gated three-adapter replay.

## Public and generated subject strata

The subject fixtures are explicitly stratified by `source_provenance_gate.csv`: 6 documentation-derived slices, 7 upstream example slices, 10 native canonical slices, 96 synthetic stress witnesses, and 1 generated canonical law probe. Synthetic stress witnesses are deterministic law-catalog probes, not independent upstream benchmarks. Raw native fixture files remain under `subjects/native_public/` and are listed in `source_manifest.csv`; the repository-level benchmark layer remains offline and deterministic.

The locked corpus is intentionally visible enough for reviewers to audit possible overfitting. Public/documentation slices, native raw fixtures, stress witnesses, generated probes, rejected transformations, unsupported transformations, and seeded controls are all separated in the ledgers. The replay does not discard unfavorable or awkward candidates after seeing adapter decisions; terminal statuses are preserved and denominator accounting is checked by the aggregate verifier.

## Generated transient files

Generated adapter fixture files under `subjects/fixtures/` are intentionally not included in the clean repository packet. They are deterministic run by-products produced by `scripts/run_full_evaluation.py` and are not required for claim verification, predicate replay, native fixture self-tests, or counterexample replay because the relevant hashes and minimized materials are preserved in the result ledgers.


## Package Creation

The release zip should be created from the repository root by running:

```bash
cd artifact
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/create_submission_zip.py ../LatticeGuard_Submission.zip
```

The packaging script includes only `paper/` and `artifact/`, excludes LaTeX/cache/transient files, and omits generated adapter fixtures under `artifact/subjects/fixtures/` because they are regenerated by replay.

The delivery-risk gate binds package hygiene, claim traceability, source provenance, adapter/reference agreement, reference integrity, PDF shape, and package consistency into one replayable closure check. `scripts/verify_final_package_gate.py` performs a cleanup sweep before the package check and reports any remaining bytecode residue explicitly.

## Hygiene and package checks

```bash
cd artifact
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/verify_all.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/verify_anonymity_and_hygiene.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/verify_final_package_gate.py
```

`verify_all.py` is the aggregate gate. `verify_anonymity_and_hygiene.py` confirms the repository stays anonymous and clean. `verify_final_package_gate.py` checks the package manifest and top-level layout without creating the delivery zip.
