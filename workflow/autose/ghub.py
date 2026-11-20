"""GitHub CLI and REST wrapper for PR creation, commenting, and CI dispatch."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

def open_pull_request(
    repo_root: str | Path,
    branch: str,
    base_branch: str,
    issue_number: int,
    title: str,
    body: str,
) -> tuple[bool, str]:
    """Create a pull request using GitHub CLI (gh)."""
    try:
        cmd = [
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--head", branch,
            "--base", base_branch,
        ]
        res = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=True)
        return True, res.stdout.strip()
    except Exception as e:
        return False, str(e)

def comment_on_pr(repo_root: str | Path, pr_url: str, comment_body: str) -> bool:
    """Post comment on an open PR."""
    try:
        cmd = ["gh", "pr", "comment", pr_url, "--body", comment_body]
        subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=True)
        return True
    except Exception:
        return False

def trigger_ci_workflow(repo_root: str | Path, branch: str, workflow_name: str = "autose-ci.yml") -> bool:
    """Explicitly trigger CI workflow because PRs opened by GITHUB_TOKEN don't trigger actions."""
    try:
        cmd = ["gh", "workflow", "run", workflow_name, "--ref", branch]
        subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=True)
        return True
    except Exception:
        return False
