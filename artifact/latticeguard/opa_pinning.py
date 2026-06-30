from __future__ import annotations
import hashlib, os, subprocess
from pathlib import Path

EXPECTED_SHA='3d4bb88482958d990351ec5d2f7558509992776bc473bc1b78d86d76cb993ca3'
LOCAL_PIN_NAME='opa_v1.17.1_linux_amd64_static'


def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _candidate_path(root: Path) -> tuple[Path, str]:
    env=os.environ.get('LG_OPA_CLI','').strip()
    if env:
        return Path(env).expanduser(), 'LG_OPA_CLI'
    return root/'tools'/LOCAL_PIN_NAME, 'artifact_tools_pin'


def inspect_opa_candidate(root: Path) -> dict[str,object]:
    path, source = _candidate_path(root)
    exists=path.exists()
    exe=exists and os.access(path, os.X_OK)
    sha=None
    version=None
    status='ABSENT'
    if exists:
        sha=_sha256(path)
        if sha != EXPECTED_SHA:
            status='HASH_MISMATCH'
        elif not exe:
            status='NOT_EXECUTABLE'
        else:
            try:
                version=subprocess.check_output([str(path),'version'], text=True, timeout=10).strip()
                status='READY'
            except Exception as e:
                version=type(e).__name__
                status='VERSION_FAILED'
    return {
        'path':str(path),
        'candidate_source':source,
        'exists':exists,
        'executable':exe,
        'sha256':sha,
        'expected_sha256':EXPECTED_SHA,
        'version':version,
        'status':status,
    }
