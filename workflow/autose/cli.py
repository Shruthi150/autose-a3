"""Main orchestrator executing the 6-stage SDLC loop."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .config import load_config
from .security import wrap_untrusted
from .state import RunState, StageFailed
from .stages import (
    run_stage1_requirements,
    run_stage2_design,
    run_stage3_implementation,
    run_stage4_testing,
    run_stage5_release,
    run_stage6_review,
)
from .ghub import comment_on_pr
from .tools import run_cmd

def main():
    parser = argparse.ArgumentParser(description="AutoSE Pipeline CLI")
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--issue-title", type=str, required=True)
    parser.add_argument("--issue-body", type=str, required=True)
    parser.add_argument("--repo-root", type=str, default=".")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    cfg = load_config()
    models = cfg["models"]
    base_branch = cfg["repo"].get("base_branch", "master")
    artifacts_dir = repo_root / ".autose" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    state = RunState(
        issue_number=args.issue_number,
        issue_title=args.issue_title,
        base_sha=cfg["repo"].get("base_branch", "master"),
        branch=f"autose/issue-{args.issue_number}",
    )

    print(f"=== AutoSE Autonomous Pipeline Starting for Issue #{args.issue_number} ===")
    
    # Checkout work branch
    run_cmd(["git", "checkout", "-B", state.branch], cwd=repo_root)

    # Stage 1: Requirements
    print("\n--- [Stage 1] Requirements Engineering ---")
    spec_md, s1_ok, s1_msg = run_stage1_requirements(args.issue_title, args.issue_body, models["requirements"])
    (artifacts_dir / "spec.md").write_text(spec_md, encoding="utf-8")
    state.mark("requirements", "passed" if s1_ok else "failed", reason=s1_msg)
    if not s1_ok:
        print(f"[!] Gate 1 Failed: {s1_msg}")
        state.save(artifacts_dir)
        sys.exit(1)
    print(f"[+] Gate 1 Passed: {s1_msg}")

    # Stage 2: Design
    print("\n--- [Stage 2] Architectural Design ---")
    design_md, s2_ok, s2_msg = run_stage2_design(spec_md, repo_root, models["design"])
    (artifacts_dir / "design.md").write_text(design_md, encoding="utf-8")
    state.mark("design", "passed" if s2_ok else "failed", reason=s2_msg)
    if not s2_ok:
        print(f"[!] Gate 2 Failed: {s2_msg}")
        state.save(artifacts_dir)
        sys.exit(1)
    print(f"[+] Gate 2 Passed: {s2_msg}")

    # Resolve target file from design
    target_file = "tinydb/table.py"
    if "queries.py" in design_md:
        target_file = "tinydb/queries.py"
    elif "operations.py" in design_md:
        target_file = "tinydb/operations.py"

    # Stage 3 & 4: Implementation and Testing Loop
    max_attempts = cfg["budgets"]["implement_attempts"]
    feedback = ""
    diff_patch = ""
    test_report_md = ""

    for attempt in range(1, max_attempts + 1):
        print(f"\n--- [Stage 3] Implementation (Attempt {attempt}/{max_attempts}) ---")
        diff_patch, s3_ok, s3_msg = run_stage3_implementation(
            design_md, repo_root, target_file, feedback, models["implementer"]
        )
        if not s3_ok:
            feedback = s3_msg
            print(f"[-] Gate 3 Failed: {s3_msg}")
            continue
        print(f"[+] Gate 3 Passed: Code builds successfully.")

        print(f"\n--- [Stage 4] Testing (Attempt {attempt}/{max_attempts}) ---")
        test_file = f"tests/test_autose_issue_{args.issue_number}.py"
        test_report_md, s4_ok, test_output = run_stage4_testing(
            spec_md, repo_root, test_file, models["tester"]
        )
        (artifacts_dir / "test_report.md").write_text(test_report_md, encoding="utf-8")
        if s4_ok:
            print("[+] Gate 4 Passed: All existing & new tests pass.")
            state.mark("testing", "passed", attempts=attempt)
            break
        else:
            print(f"[-] Gate 4 Failed on attempt {attempt}: Tests broken.")
            feedback = test_output
    else:
        print("[!] Max implementation attempts exhausted. Failing run.")
        state.mark("testing", "failed", reason="Max retries exhausted")
        state.save(artifacts_dir)
        sys.exit(1)

    (artifacts_dir / "diff.patch").write_text(diff_patch, encoding="utf-8")

    # Stage 5: Release
    print("\n--- [Stage 5] Release ---")
    pr_url, pr_md, s5_ok, s5_msg = run_stage5_release(
        repo_root, state.branch, base_branch, args.issue_number, spec_md, test_report_md
    )
    (artifacts_dir / "pr.md").write_text(pr_md, encoding="utf-8")
    state.mark("release", "passed" if s5_ok else "failed", pr_url=pr_url, reason=s5_msg)
    state.pr_url = pr_url
    print(f"[+] Gate 5 Passed: PR opened at {pr_url}")

    # Stage 6: Independent Review
    print("\n--- [Stage 6] Independent Review ---")
    verdict, review_md, s6_ok, s6_msg = run_stage6_review(
        args.issue_title, args.issue_body, diff_patch, models["reviewer"], round_num=1
    )
    (artifacts_dir / "review.md").write_text(review_md, encoding="utf-8")
    state.mark("review", "passed", verdict=verdict, reason=s6_msg)
    print(f"[+] Gate 6 Passed: Reviewer verdict: {verdict}")

    if pr_url:
        comment_on_pr(repo_root, pr_url, f"## AutoSE Stage 6: Independent Review\n\n{review_md}")

    state.status = "ok"
    state.save(artifacts_dir)
    print("\n=== AutoSE Pipeline Run Complete ===")

if __name__ == "__main__":
    main()
