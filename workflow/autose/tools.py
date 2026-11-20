"""Role-based tools and sandboxed operations for each stage."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .security import scrubbed_env

def run_cmd(cmd: list[str], cwd: str | Path, timeout: int = 120) -> tuple[int, str, str]:
    """Execute command in scrubbed environment with timeout."""
    res = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=scrubbed_env(),
    )
    return res.returncode, res.stdout, res.stderr

def run_tests(repo_root: str | Path, test_file: str | None = None) -> tuple[bool, str]:
    """Execute pytest suite."""
    cmd = ["python", "-m", "pytest", "-v", "-p", "no:cacheprovider"]
    if test_file:
        cmd.append(test_file)
    ret, stdout, stderr = run_cmd(cmd, cwd=repo_root, timeout=180)
    output = f"{stdout}\n{stderr}".strip()
    return (ret == 0), output

def compile_check(repo_root: str | Path, target_files: list[str]) -> tuple[bool, str]:
    """Check Python syntax and build."""
    for rel_path in target_files:
        p = Path(repo_root) / rel_path
        if p.suffix == ".py":
            cmd = ["python", "-m", "py_compile", str(p)]
            ret, out, err = run_cmd(cmd, cwd=repo_root)
            if ret != 0:
                return False, f"Syntax / compilation error in {rel_path}:\n{err}\n{out}"
    return True, "All files compiled successfully."
