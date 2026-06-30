from __future__ import annotations
BASELINES = [
 ('UPSTREAM_ONLY','Native/public examples without metamorphic transformations'),
 ('CROSS_ADAPTER_DIFFERENTIAL_ONLY','Compare normalized Casbin/Cedar decisions without laws'),
 ('CROSS_VERSION_DIFFERENTIAL_PRECHECK','Release-pair differential harness with no real drift claim unless a vetted pair is replayed'),
 ('SINGLE_RELATION','Isolate one relation family at a time'),
 ('NO_APPLICABILITY_GATE','Ablate rejection and show unsound denominator risk'),
 ('RANDOM_VALID_PERTURB','Budget-matched valid perturbations without typed law'),
 ('PROPERTY_GENERATOR_NO_REJECTION','Property-style generation without invalid-transformation rejection'),
 ('LATTICEGUARD_FULL_ORACLE','Full applicability-checked law oracle'),
 ('SEEDED_MUTANT_POSITIVE_CONTROL','Semantic-drift controls for hierarchy/deny faults'),
]

def baseline_rows() -> list[dict[str,str]]: return [{'baseline_id':a,'purpose':b} for a,b in BASELINES]
def validate_baselines() -> list[str]: return [] if len(BASELINES)>=8 else ['too few baselines']
