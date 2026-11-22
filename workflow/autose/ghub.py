"""GitHub CLI wrapper for PR creation/reuse, commenting, and CI dispatch + polling."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path


def find_open_pr(repo_root: str | Path, branch: str) -> tuple[int, str]:
    """Return (pr_number, pr_url) if an open PR already exists for branch, else (0, '')."""
    try:
        res = subprocess.run(
            ["gh", "pr", "list", "--head", branch, "--state", "open", "--json", "number,url"],
            cwd=str(repo_root), capture_output=True, text=True, check=True,
        )
        items = json.loads(res.stdout or "[]")
        if items:
            return int(items[0]["number"]), str(items[0]["url"])
    except Exception:
        pass
    return 0, ""


def open_pull_request(
    repo_root: str | Path,
    branch: str,
    base_branch: str,
    issue_number: int,
    title: str,
    body: str,
) -> tuple[bool, int, str]:
    """Create a pull request (or reuse an existing open PR for the branch)."""
    pr_num, pr_url = find_open_pr(repo_root, branch)
    if pr_url:
        subprocess.run(
            ["gh", "pr", "edit", str(pr_num), "--title", title, "--body", body],
            cwd=str(repo_root), capture_output=True, text=True, check=False,
        )
        return True, pr_num, pr_url

    try:
        res = subprocess.run(
            ["gh", "pr", "create", "--title", title, "--body", body, "--head", branch, "--base", base_branch],
            cwd=str(repo_root), capture_output=True, text=True, check=True,
        )
        pr_url = res.stdout.strip().splitlines()[-1].strip()
        pr_num, _ = find_open_pr(repo_root, branch)
        if not pr_num and "/pull/" in pr_url:
            try:
                pr_num = int(pr_url.rstrip("/").split("/")[-1])
            except ValueError:
                pr_num = 0
        return True, pr_num, pr_url
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        return False, 0, err
    except Exception as e:
        return False, 0, str(e)


def comment_on_pr(repo_root: str | Path, pr_ref: str | int, comment_body: str) -> bool:
    """Post a comment on an open PR."""
    try:
        subprocess.run(
            ["gh", "pr", "comment", str(pr_ref), "--body", comment_body],
            cwd=str(repo_root), capture_output=True, text=True, check=True,
        )
        return True
    except Exception as e:
        print(f"[autose-gh] Failed to comment on PR {pr_ref}: {e}", flush=True)
        return False


def trigger_and_wait_ci(
    repo_root: str | Path,
    branch: str,
    workflow_name: str = "autose-ci.yml",
    wait_seconds: int = 180,
) -> tuple[bool, str]:
    """Dispatch autose-ci.yml on branch (PRs opened by GITHUB_TOKEN don't trigger CI) and wait for completion."""
    try:
        subprocess.run(
            ["gh", "workflow", "run", workflow_name, "--ref", branch],
            cwd=str(repo_root), capture_output=True, text=True, check=True,
        )
    except Exception as e:
        return False, f"Failed to dispatch {workflow_name}: {e}"

    deadline = time.time() + wait_seconds
    time.sleep(6)  # give GitHub a moment to register the run
    while time.time() < deadline:
        try:
            res = subprocess.run(
                [
                    "gh", "run", "list",
                    "--workflow", workflow_name,
                    "--branch", branch,
                    "--limit", "1",
                    "--json", "databaseId,status,conclusion,url",
                ],
                cwd=str(repo_root), capture_output=True, text=True, check=True,
            )
            runs = json.loads(res.stdout or "[]")
            if runs:
                run = runs[0]
                status = run.get("status", "")
                conclusion = run.get("conclusion", "")
                url = run.get("url", "")
                if status == "completed":
                    return (conclusion == "success"), f"CI {conclusion}: {url}"
        except Exception:
            pass
        time.sleep(8)
    return False, f"Timed out waiting {wait_seconds}s for {workflow_name} on {branch}"
