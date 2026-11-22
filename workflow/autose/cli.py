"""Deterministic orchestrator for AutoSE SDLC stages (ADR-002).

Supports three subcommands so GitHub Actions can enforce job-level permission separation:
  * build   : Stages 1-5 (write permissions: creates branch, edits, tests, opens PR, waits for CI)
  * review  : Stage 6 only (read-only code perms: independent reviewer in a separate job)
  * rework  : Rework after REQUEST_CHANGES (write perms: routes to Stage 2 on APPROACH or Stage 3 on CODE)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .config import load_config
from .ghub import comment_on_pr
from .llm import set_token_hook
from .stages import (
    design_files,
    run_stage1_requirements,
    run_stage2_design,
    run_stage3_implementation,
    run_stage4_testing,
    run_stage5_release,
    run_stage6_review,
)
from .state import RunState
from .tools import run_cmd, run_tests


def _write_gh_output(pairs: dict[str, str]) -> None:
    out_file = os.environ.get("GITHUB_OUTPUT")
    if not out_file:
        return
    with open(out_file, "a", encoding="utf-8") as fh:
        for k, v in pairs.items():
            fh.write(f"{k}={v}\n")


def _fail(state: RunState, art: Path, stage: str, reason: str) -> None:
    state.status, state.failed_stage, state.failure_reason = "failed", stage, reason
    state.save(art)
    (art / "FAILED.md").write_text(f"# Run stopped at stage: {stage}\n\n{reason}\n", encoding="utf-8")
    print(f"[!] {stage} failed: {reason}", flush=True)
    sys.exit(1)


def _detect_base_branch(repo_root: Path, cfg_base: str) -> str:
    env_base = os.environ.get("BASE_BRANCH", "").strip()
    if env_base:
        return env_base
    rc, out, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    head = out.strip()
    if rc == 0 and head in ("main", "master"):
        return head
    return cfg_base


def cmd_build(args: argparse.Namespace) -> None:
    root = Path(args.repo_root).resolve()
    cfg = load_config()
    models = cfg["models"]
    base = _detect_base_branch(root, cfg["repo"]["base_branch"])
    art = root / ".autose" / "artifacts"
    art.mkdir(parents=True, exist_ok=True)

    title = args.issue_title or os.environ.get("ISSUE_TITLE", "")
    body = args.issue_body or os.environ.get("ISSUE_BODY", "")
    branch = f"autose/issue-{args.issue_number}"

    state = RunState(
        repo=os.environ.get("GITHUB_REPOSITORY", ""),
        run_id=os.environ.get("GITHUB_RUN_ID", ""),
        issue_number=args.issue_number,
        issue_title=title,
        base_sha=base,
        branch=branch,
    )
    set_token_hook(state.add_tokens)
    run_cmd(["git", "checkout", "-B", branch], cwd=root)

    # Stage 1: Requirements
    state.event("requirements", "start")
    spec, ok, why = run_stage1_requirements(title, body, models["requirements"])
    (art / "spec.md").write_text(spec, encoding="utf-8")
    state.mark("requirements", "passed" if ok else "failed", reason=why)
    if not ok:
        _fail(state, art, "requirements", why)

    # Stage 2: Design
    state.event("design", "start")
    design, ok, why = run_stage2_design(spec, root, models["design"])
    (art / "design.md").write_text(design, encoding="utf-8")
    state.mark("design", "passed" if ok else "failed", reason=why)
    if not ok:
        _fail(state, art, "design", why)
    targets = design_files(design, root)

    # Stage 3 & 4: Implementation <-> Testing loop
    feedback, diff, report = "", "", ""
    attempts = cfg["budgets"]["implement_attempts"]
    test_file = f"tests/test_autose_issue_{args.issue_number}.py"
    for n in range(1, attempts + 1):
        state.event("implementation", f"attempt-{n}")
        diff, ok, why = run_stage3_implementation(design, root, targets, feedback, models["implementer"])
        print(f"[stage3 attempt {n}] ok={ok} {why[:200]}", flush=True)
        if not ok:
            feedback = why
            continue
        state.event("testing", f"attempt-{n}")
        report, ok, out = run_stage4_testing(spec, root, test_file, models["tester"], feedback)
        (art / "test_report.md").write_text(report, encoding="utf-8")
        print(f"[stage4 attempt {n}] ok={ok}", flush=True)
        if ok:
            state.mark("implementation", "passed", attempts=n)
            state.mark("testing", "passed", attempts=n)
            break
        tail = "\n".join(out.splitlines()[-12:])
        print(f"[stage4 attempt {n} tail]\n{tail}", flush=True)
        feedback = out
    else:
        _fail(state, art, "testing", f"No passing implementation after {attempts} attempts.\n\n{feedback[-3000:]}")

    (art / "diff.patch").write_text(diff, encoding="utf-8")
    if args.no_release:
        state.status = "ok"
        state.save(art)
        print(f"[dry run] stopped before release. total_tokens={state.total_tokens}", flush=True)
        return

    # Stage 5: Release + CI check
    state.event("release", "start")
    pr_num, pr_url, pr_md, ok, why = run_stage5_release(root, branch, base, args.issue_number, spec, report)
    (art / "pr.md").write_text(pr_md, encoding="utf-8")
    state.mark("release", "passed" if ok else "failed", pr_number=pr_num, pr_url=pr_url, reason=why)
    state.pr_number, state.pr_url = pr_num, pr_url
    if not ok:
        _fail(state, art, "release", why)

    state.save(art)
    _write_gh_output({
        "pr_number": str(pr_num),
        "pr_url": pr_url,
        "branch": branch,
        "base_branch": base,
    })
    print(f"[stage5] PR #{pr_num} open and CI passed: {pr_url} (tokens={state.total_tokens})", flush=True)


def cmd_review(args: argparse.Namespace) -> None:
    """Stage 6: Independent reviewer. Runs in its own read-only job with zero implementer context."""
    root = Path(args.repo_root).resolve()
    cfg = load_config()
    art = root / ".autose" / "artifacts"
    art.mkdir(parents=True, exist_ok=True)

    title = args.issue_title or os.environ.get("ISSUE_TITLE", "")
    body = args.issue_body or os.environ.get("ISSUE_BODY", "")
    base = args.base_branch or os.environ.get("BASE_BRANCH", cfg["repo"]["base_branch"])

    tokens = {"input": 0, "output": 0}
    set_token_hook(lambda i, o: (tokens.__setitem__("input", tokens["input"] + i),
                                 tokens.__setitem__("output", tokens["output"] + o)))

    # Reviewer computes the diff directly from git against base branch (never trusts implementer artifacts)
    _, diff_patch, _ = run_cmd(["git", "diff", f"origin/{base}...HEAD", "--", "tinydb", "tests"], cwd=root)
    if not diff_patch.strip():
        _, diff_patch, _ = run_cmd(["git", "diff", "HEAD~1..HEAD", "--", "tinydb", "tests"], cwd=root)

    # Reviewer runs pytest itself in read-only checkout
    test_ok, test_out = run_tests(root)
    pytest_summary = f"pytest_passed={test_ok}\n{test_out}"

    verdict, category, review_md, _, summary = run_stage6_review(
        title, body, diff_patch, cfg["models"]["reviewer"], args.round, pytest_output=pytest_summary
    )
    fname = "review.md" if args.round == 1 else f"review_round_{args.round}.md"
    (art / fname).write_text(review_md, encoding="utf-8")

    pr_ref = args.pr_number or os.environ.get("PR_NUMBER", "")
    if pr_ref:
        comment_on_pr(
            root,
            pr_ref,
            f"## AutoSE Independent Review (Round {args.round}/2)\n\n"
            f"- **Verdict**: `{verdict}` (`{category}`)\n"
            f"- **Reviewer pytest check**: `{'PASS' if test_ok else 'FAIL'}`\n\n"
            f"{review_md}",
        )

    _write_gh_output({"verdict": verdict, "category": category})
    print(f"[stage6] {summary} (reviewer_tokens={tokens['input'] + tokens['output']})", flush=True)


def cmd_rework(args: argparse.Namespace) -> None:
    """Rework after reviewer REQUEST_CHANGES. Routes to Design (APPROACH) or Implementation (CODE)."""
    root = Path(args.repo_root).resolve()
    cfg = load_config()
    models = cfg["models"]
    art = root / ".autose" / "artifacts"
    base = args.base_branch or os.environ.get("BASE_BRANCH", cfg["repo"]["base_branch"])
    branch = args.branch or f"autose/issue-{args.issue_number}"

    state = RunState.load(art) if (art / "state.json").exists() else RunState(issue_number=args.issue_number, branch=branch)
    set_token_hook(state.add_tokens)

    spec = (art / "spec.md").read_text(encoding="utf-8")
    design = (art / "design.md").read_text(encoding="utf-8")
    review = (art / "review.md").read_text(encoding="utf-8")

    if args.category == "APPROACH":
        state.event("design", "rework")
        design, ok, why = run_stage2_design(spec, root, models["design"], feedback=review)
        (art / "design.md").write_text(design, encoding="utf-8")
        if not ok:
            _fail(state, art, "design-rework", why)

    targets = design_files(design, root)
    test_file = f"tests/test_autose_issue_{args.issue_number}.py"
    feedback = f"Reviewer requested changes:\n{review}"
    diff, report = "", ""
    for n in range(1, 3):
        diff, ok, why = run_stage3_implementation(design, root, targets, feedback, models["implementer"])
        if not ok:
            feedback = why
            continue
        report, ok, out = run_stage4_testing(spec, root, test_file, models["tester"], feedback)
        (art / "test_report.md").write_text(report, encoding="utf-8")
        if ok:
            break
        feedback = out
    else:
        _fail(state, art, "rework", f"Rework failed tests:\n{feedback[-2000:]}")

    (art / "diff.patch").write_text(diff, encoding="utf-8")
    _, pr_url, pr_md, ok, why = run_stage5_release(
        root, branch, base, args.issue_number, spec, report, commit_msg=f"AutoSE: address review feedback for #{args.issue_number}"
    )
    (art / "pr.md").write_text(pr_md, encoding="utf-8")
    state.save(art)
    if not ok:
        _fail(state, art, "rework-release", why)
    print(f"[rework] pushed updated PR {pr_url} (total_tokens={state.total_tokens})", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="AutoSE Pipeline CLI")
    sub = ap.add_subparsers(dest="command")

    p_build = sub.add_parser("build")
    p_build.add_argument("--issue-number", type=int, required=True)
    p_build.add_argument("--issue-title", default="")
    p_build.add_argument("--issue-body", default="")
    p_build.add_argument("--repo-root", default=".")
    p_build.add_argument("--no-release", action="store_true")

    p_rev = sub.add_parser("review")
    p_rev.add_argument("--issue-number", type=int, required=True)
    p_rev.add_argument("--issue-title", default="")
    p_rev.add_argument("--issue-body", default="")
    p_rev.add_argument("--pr-number", type=int, default=0)
    p_rev.add_argument("--base-branch", default="")
    p_rev.add_argument("--round", type=int, default=1)
    p_rev.add_argument("--repo-root", default=".")

    p_rw = sub.add_parser("rework")
    p_rw.add_argument("--issue-number", type=int, required=True)
    p_rw.add_argument("--branch", default="")
    p_rw.add_argument("--base-branch", default="")
    p_rw.add_argument("--category", default="CODE")
    p_rw.add_argument("--repo-root", default=".")

    args = ap.parse_args()
    if args.command == "build":
        cmd_build(args)
    elif args.command == "review":
        cmd_review(args)
    elif args.command == "rework":
        cmd_rework(args)
    else:
        ap.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
