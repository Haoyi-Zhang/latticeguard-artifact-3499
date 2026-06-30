from __future__ import annotations
from pathlib import Path
from .repo_quality import count_python_lines, hygiene_scan
from .evidence_queries import summarize_evidence

READINESS_THRESHOLDS={
    'python_lines':4904,
    'evaluated_obligations':400,
    'native_benchmark_sources':10,
    'model_check_cases':70000,
    'native_selftests':30,
    'source_count':17,
}

def readiness_report(root: Path) -> dict[str,object]:
    metrics=count_python_lines(root); evidence=summarize_evidence(root); hygiene=hygiene_scan(root.parent)
    checks={
        'python_lines': metrics['python_lines']>=READINESS_THRESHOLDS['python_lines'],
        'evaluated_obligations': evidence['evaluated_obligations']>=READINESS_THRESHOLDS['evaluated_obligations'],
        'native_benchmark_sources': evidence['native_benchmark_sources']>=READINESS_THRESHOLDS['native_benchmark_sources'],
        'model_check_cases': evidence['model_check_cases']>=READINESS_THRESHOLDS['model_check_cases'],
        'native_selftests': evidence['native_selftests']>=READINESS_THRESHOLDS['native_selftests'],
        'source_count': evidence['sources']>=READINESS_THRESHOLDS['source_count'],
        'hygiene': not hygiene,
    }
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'metrics':metrics,'evidence':evidence,'hygiene_issues':hygiene}
