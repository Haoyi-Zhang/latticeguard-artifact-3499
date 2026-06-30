from __future__ import annotations

import os
import shutil
from pathlib import Path

BYTECODE_DIR_NAME = "__pycache__"
BYTECODE_SUFFIXES = {".pyc", ".pyo"}


def python_bytecode_env(base: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base or os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def scan_bytecode_artifacts(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        if BYTECODE_DIR_NAME in path.parts or (path.is_file() and path.suffix in BYTECODE_SUFFIXES):
            paths.append(path)
    return sorted(paths, key=lambda p: p.as_posix())


def cleanup_bytecode_artifacts(root: Path) -> list[str]:
    removed: list[str] = []
    paths = scan_bytecode_artifacts(root)
    files = [path for path in paths if path.is_file()]
    dirs = [path for path in paths if path.is_dir()]
    for path in files:
        removed.append(path.relative_to(root).as_posix())
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    for path in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
        removed.append(path.relative_to(root).as_posix())
        shutil.rmtree(path, ignore_errors=True)
    return removed
