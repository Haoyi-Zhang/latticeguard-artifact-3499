# OPA/Rego CLI pinning contract

The artifact contains an implemented OPA/Rego adapter and the current locked run
counts it through a vetted OPA executable. The primary run must not use an
arbitrary system OPA. The counted executable path is:

```
artifact/tools/opa_v1.17.1_linux_amd64_static
```

`LG_OPA_CLI` may point to an equivalent vetted executable. The executable must be
non-empty, executable, and SHA-256-identical to the checksum recorded by
`latticeguard/opa_pinning.py` before any OPA obligation row is observed. If the
pinning check fails, OPA is excluded before results and the denominator is
recomputed. The complete evaluation and claim-verification chain must pass before
the artifact can count OPA as executed.
