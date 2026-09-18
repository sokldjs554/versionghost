from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


class WorkspaceError(RuntimeError):
    pass


def create_workspace(source_root: Path, run_root: Path) -> Path:
    workspace = run_root / "workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    source_sample = source_root / "sample_app"
    if not source_sample.exists():
        raise WorkspaceError(f"Missing sample_app at {source_sample}")
    shutil.copytree(source_sample, workspace / "sample_app")
    return workspace


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
