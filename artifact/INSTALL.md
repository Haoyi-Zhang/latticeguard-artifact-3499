# LatticeGuard Install and Replay Notes

LatticeGuard is an offline, CPU-only artifact. It does not require a GPU, cloud account, commercial API, private dataset, hosted service, or network scan for replay.

## Platform

- Linux x86_64/amd64.
- Python 3.13.
- Run commands from the `artifact/` directory.
- Vendored Python packages are under `vendor_python/`; `requirements.txt` records the pinned versions used to build the packet.
- The Cedar bridge bundled in this packet is a CPython 3.13 native extension. Other Python versions require rebuilding the same pinned package outside the clean packet.

## Environment Check

```bash
cd artifact
python3.13 --version
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/preflight_external_tools.py
```

The preflight command should report a passing local adapter/tool state. OPA/Rego rows enter the denominator only if the shipped CLI executable passes the SHA-256 pinning contract in `tools/OPA_PINNING.md`.

## Full Replay

```bash
cd artifact
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/run_full_evaluation.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/verify_all.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/verify_robustness_replay.py
PYTHONDONTWRITEBYTECODE=1 python3.13 -B scripts/verify_all.py
```

Each verification command should print JSON with `"status": "PASS"`. The replay is deterministic; bytecode caches are disabled and package checks remove Python cache residue before integrity checks.

## Interpreting the Result

The headline primary run is a regression-oracle result over the declared supported fragments. A passing primary row means the enabled adapter decision satisfies a law-specific invariant for an applicable candidate. Rejected rows and unsupported rows are preserved as evidence but excluded from the pass denominator. Seeded semantic drifts exercise failure detection and minimization; they are positive controls, not discovered implementation defects.

The `results/validity_challenge_evidence.csv/json` files summarize the artifact's main construct-validity guards: OPA boundary handling, outcome-independent holdout coverage, zero-failure sensitivity, denominator-pressure accounting, source-stratum separation, public/native fixture validation, and disclosure scope.
