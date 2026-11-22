"""Deterministic orchestrator for the six stages (ADR-002)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .ghub import comment_on_pr
from .state import RunState
from .stages import (design_files, run_stage1_requirements, run_stage2_design, run_stage3_implementation,
                     run_stage4_testing, run_stage5_release, run_stage6_review)
from .tools import run_cmd


def fail(state: RunState, art: Path, stage: str, reason: str) -> None:
    state.status, state.failed_stage, state.failure_reason = "failed", stage, reason
    state.save(art)
    (art / "FAILED.md").write_text(f"# Run stopped at stage: {stage}\n\n{reason}\n", encoding="utf-8")
    print(f"[!] {stage} failed: {reason}")
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue-number", type=int, required=True)
    ap.add_argument("--issue-title", required=True)
    ap.add_argument("--issue-body", required=True)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--no-release", action="store_true", help="stop after stage 4 (local dry run)")
    a = ap.parse_args()

    root = Path(a.repo_root).resolve()
    cfg = load_config()
    models, base = cfg["models"], cfg["repo"]["base_branch"]
    art = root / ".autose" / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    state = RunState(issue_number=a.issue_number, issue_title=a.issue_title, branch=f"autose/issue-{a.issue_number}")
    run_cmd(["git", "checkout", "-B", state.branch], cwd=root)

    spec, ok, why = run_stage1_requirements(a.issue_title, a.issue_body, models["requirements"])
    (art / "spec.md").write_text(spec, encoding="utf-8")
    state.mark("requirements", "passed" if ok else "failed", reason=why)
    if not ok:
        fail(state, art, "requirements", why)

    design, ok, why = run_stage2_design(spec, root, models["design"])
    (art / "design.md").write_text(design, encoding="utf-8")
    state.mark("design", "passed" if ok else "failed", reason=why)
    if not ok:
        fail(state, art, "design", why)
    targets = design_files(design, root)

    feedback, diff, report = "", "", ""
    attempts = cfg["budgets"]["implement_attempts"]
    test_file = f"tests/test_autose_issue_{a.issue_number}.py"
    for n in range(1, attempts + 1):
        diff, ok, why = run_stage3_implementation(design, root, targets, feedback, models["implementer"])
        print(f"[stage3 attempt {n}] ok={ok} {why[:200]}")
        if not ok:
            feedback = why
            continue
        report, ok, out = run_stage4_testing(spec, root, test_file, models["tester"], feedback)
        (art / "test_report.md").write_text(report, encoding="utf-8")
        print(f"[stage4 attempt {n}] ok={ok}")
        if ok:
            state.mark("implementation", "passed", attempts=n)
            state.mark("testing", "passed", attempts=n)
            break
        feedback = out
    else:
        fail(state, art, "testing", f"No passing implementation after {attempts} attempts.\n\n{feedback[-3000:]}")
    (art / "diff.patch").write_text(diff, encoding="utf-8")
    if a.no_release:
        state.save(art)
        print("[dry run] stopped before release")
        return

    pr_url, pr_md, ok, why = run_stage5_release(root, state.branch, base, a.issue_number, spec, report)
    (art / "pr.md").write_text(pr_md, encoding="utf-8")
    state.mark("release", "passed" if ok else "failed", pr_url=pr_url)
    if not ok:
        fail(state, art, "release", why)
    state.pr_url = pr_url

    rounds = cfg["budgets"]["max_review_rounds"]
    for r in range(1, rounds + 1):
        verdict, review, done, why = run_stage6_review(a.issue_title, a.issue_body, diff, models["reviewer"], r)
        (art / "review.md").write_text(review, encoding="utf-8")
        state.reviews.append({"round": r, "verdict": verdict})
        comment_on_pr(root, pr_url, f"## AutoSE independent review (round {r}/{rounds})\n\n{review}")
        if verdict == "APPROVE" or r == rounds:
            break
        # Request changes: go back to implementation with the reviewer's findings, then re-test and re-push.
        diff, ok, why = run_stage3_implementation(design, root, targets, review, models["implementer"])
        if not ok:
            break
        report, ok, out = run_stage4_testing(spec, root, test_file, models["tester"], review)
        if not ok:
            break
        run_cmd(["git", "add", "tinydb", "tests"], cwd=root)
        run_cmd(["git", "commit", "-m", f"AutoSE: address review round {r}"], cwd=root)
        run_cmd(["git", "push", "origin", state.branch], cwd=root)
    state.mark("review", "passed", verdict=state.reviews[-1]["verdict"])
    state.status = "ok"
    state.save(art)
    print("done; a human decides whether to merge.")


if __name__ == "__main__":
    main()
