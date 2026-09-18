from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from versionghost.models import CheckResult


def run_python_tests(repo_root: Path) -> CheckResult:
    start = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)
    proc = subprocess.run(
        ["python", "-m", "pytest", "-q", "sample_app/liveops_service/tests"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    duration = int((time.perf_counter() - start) * 1000)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return CheckResult(
        name="target-unit-tests",
        status="pass" if proc.returncode == 0 else "fail",
        detail=output[-3000:] or f"exit={proc.returncode}",
        duration_ms=duration,
    )


def run_compile_check(repo_root: Path) -> CheckResult:
    start = time.perf_counter()
    proc = subprocess.run(
        ["python", "-m", "compileall", "-q", "sample_app/liveops_service"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    duration = int((time.perf_counter() - start) * 1000)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return CheckResult(
        name="compile-check",
        status="pass" if proc.returncode == 0 else "fail",
        detail=output or "Python source compiled successfully.",
        duration_ms=duration,
    )
