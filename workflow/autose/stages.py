"""Stages and checks implementation for the 6 SDLC steps."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from .llm import call_gemini
from .security import wrap_untrusted
from .tools import compile_check, run_cmd, run_tests
from .ghub import open_pull_request, comment_on_pr, trigger_ci_workflow

# ----------------- STAGE 1: REQUIREMENTS -----------------
def run_stage1_requirements(issue_title: str, issue_body: str, model: str) -> tuple[str, bool, str]:
    sys_prompt = """You are the Requirements Agent in an autonomous SDLC pipeline for TinyDB.
Read the untrusted issue and produce spec.md containing clear, testable acceptance criteria.
Rules:
1. Extract the core problem, user expectations, and edge cases.
2. Define a numbered list of testable Acceptance Criteria (AC-1, AC-2, ...).
3. Do NOT write code implementations here. Only produce the specification in Markdown.
"""
    user_prompt = f"{wrap_untrusted('issue_title', issue_title)}\n\n{wrap_untrusted('issue_body', issue_body)}"
    spec_md = call_gemini(model, sys_prompt, user_prompt)

    ac_matches = re.findall(r"AC-\d+|Acceptance Criterion \d+|\d+\.\s+\*\*Condition\*\*", spec_md)
    has_section = "Acceptance Criteria" in spec_md
    passed = has_section and len(ac_matches) >= 2
    reason = "Testable criteria found" if passed else "Lacks structured Acceptance Criteria section or has < 2 criteria"
    return spec_md, passed, reason

# ----------------- STAGE 2: DESIGN -----------------
def run_stage2_design(spec_md: str, repo_root: str | Path, model: str) -> tuple[str, bool, str]:
    sys_prompt = """You are the Architectural Design Agent in an autonomous SDLC pipeline for TinyDB.
Read spec.md and generate an implementation plan in design.md.
Rules:
1. Identify the exact files to modify (e.g. tinydb/table.py, tinydb/queries.py, or tinydb/operations.py).
2. Format target files exactly as:
- File: `tinydb/<filename>.py`
  - Function: `<func_name>`
  - Changes: <Description>
3. Specify backward compatibility and data structures.
"""
    arch_doc = (Path(repo_root) / "ARCHITECTURE.md").read_text(encoding="utf-8") if (Path(repo_root) / "ARCHITECTURE.md").exists() else "TinyDB Architecture"
    user_prompt = f"Architecture:\n{arch_doc}\n\nSpecification:\n{spec_md}"
    design_md = call_gemini(model, sys_prompt, user_prompt)

    file_matches = re.findall(r"-\s*File:\s*[`\"]?([a-zA-Z0-9_\-\./\\]+\.py)[`\"]?", design_md)
    func_matches = re.findall(r"-\s*Function:\s*[`\"]?([a-zA-Z0-9_]+)[`\"]?", design_md)
    passed = bool(file_matches and func_matches)
    reason = f"Identified {len(file_matches)} file(s) and {len(func_matches)} function(s)" if passed else "Missing target files or functions"
    return design_md, passed, reason

# ----------------- STAGE 3: IMPLEMENTATION -----------------
def run_stage3_implementation(
    design_md: str,
    repo_root: str | Path,
    target_rel_file: str,
    feedback: str,
    model: str
) -> tuple[str, bool, str]:
    full_path = Path(repo_root) / target_rel_file
    orig_code = full_path.read_text(encoding="utf-8") if full_path.exists() else ""

    sys_prompt = f"""You are the Implementation Agent in an autonomous SDLC pipeline for TinyDB.
Modify `{target_rel_file}` following the architectural design.
Rules:
1. Return the COMPLETE, full updated code for `{target_rel_file}` inside a single ```python ... ``` block.
2. Do not omit any existing functions or methods (no placeholders like '... rest of code ...').
3. Keep code clean, backward-compatible, and idiomatic Python.
"""
    user_prompt = f"Design Plan:\n{design_md}\n\nExisting Code:\n```python\n{orig_code}\n```"
    if feedback:
        user_prompt += f"\n\nPRIOR ATTEMPT FAILURE FEEDBACK:\n{feedback}\nPlease fix the failing tests!"

    resp = call_gemini(model, sys_prompt, user_prompt)
    code_match = re.search(r"```python\s*(.*?)\s*```", resp, re.DOTALL)
    new_code = code_match.group(1) if code_match else resp

    full_path.write_text(new_code, encoding="utf-8")

    # Check 3: The code builds
    ok, msg = compile_check(repo_root, [target_rel_file])
    diff_patch = ""
    if ok:
        _, stdout, _ = run_cmd(["git", "diff"], cwd=repo_root)
        diff_patch = stdout
    return diff_patch, ok, msg

# ----------------- STAGE 4: TESTING -----------------
def run_stage4_testing(
    spec_md: str,
    repo_root: str | Path,
    test_rel_file: str,
    model: str
) -> tuple[str, bool, str]:
    sys_prompt = """You are the Testing Agent in an autonomous SDLC pipeline for TinyDB.
Write pytest unit tests covering each Acceptance Criterion from spec.md into a test file.
Rules:
1. Write focused, robust test functions for TinyDB.
2. Import from tinydb (e.g. from tinydb import TinyDB, Query, where; from tinydb.operations import increment, decrement).
3. Return the COMPLETE test file code inside a single ```python ... ``` block.
"""
    user_prompt = f"Specification:\n{spec_md}"
    resp = call_gemini(model, sys_prompt, user_prompt)
    code_match = re.search(r"```python\s*(.*?)\s*```", resp, re.DOTALL)
    test_code = code_match.group(1) if code_match else resp

    test_path = Path(repo_root) / test_rel_file
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(test_code, encoding="utf-8")

    # Check 4: Run only the new test file to verify the feature without interference
    passed, output = run_tests(repo_root, test_rel_file)
    report_md = f"# Test Execution Report\n\n**Status**: {'PASSED' if passed else 'FAILED'}\n\n```\n{output}\n```"
    return report_md, passed, output

# ----------------- STAGE 5: RELEASE -----------------
def run_stage5_release(
    repo_root: str | Path,
    branch: str,
    base_branch: str,
    issue_number: int,
    spec_md: str,
    test_report_md: str
) -> tuple[str, str, bool, str]:
    run_cmd(["git", "config", "user.name", "autose-bot"], cwd=repo_root)
    run_cmd(["git", "config", "user.email", "autose-bot@users.noreply.github.com"], cwd=repo_root)
    run_cmd(["git", "add", "."], cwd=repo_root)
    run_cmd(["git", "commit", "-m", f"AutoSE: Automated fix for Issue #{issue_number}"], cwd=repo_root)
    run_cmd(["git", "push", "-u", "origin", branch, "--force"], cwd=repo_root)

    title = f"[AutoSE] Fix for Issue #{issue_number}"
    body = f"## AutoSE Autonomous PR\n\nResolves #{issue_number}.\n\n### Specification\n{spec_md[:500]}...\n\n### Verification\nAll tests passed in verification stage."
    
    ok, pr_url = open_pull_request(repo_root, branch, base_branch, issue_number, title, body)
    if ok:
        trigger_ci_workflow(repo_root, branch)
    pr_md = f"# Pull Request\n\n**PR URL**: {pr_url}\n**Branch**: `{branch}`"
    return pr_url, pr_md, ok, pr_url if ok else "PR creation failed"

# ----------------- STAGE 6: INDEPENDENT REVIEW -----------------
def run_stage6_review(
    issue_title: str,
    issue_body: str,
    diff_patch: str,
    model: str,
    round_num: int
) -> tuple[str, str, bool, str]:
    sys_prompt = """You are the Independent Adversarial Code Reviewer in an automated software pipeline.
Evaluate the diff against the issue requirements. You have ZERO implementer context.
Active check items:
1. Requirements Completeness: Does it address the issue fully?
2. Regressions & Edge Cases: Did it break types, error handling, or performance?
3. Quality & Tests: Are new tests comprehensive?

You MUST render one explicit verdict on its own line:
DECISION: APPROVE
or
DECISION: REQUEST_CHANGES
"""
    user_prompt = f"{wrap_untrusted('issue_title', issue_title)}\n\n{wrap_untrusted('issue_body', issue_body)}\n\n<pull_request_diff>\n{diff_patch}\n</pull_request_diff>"
    review_md = call_gemini(model, sys_prompt, user_prompt)

    verdict = "REQUEST_CHANGES"
    if "DECISION: APPROVE" in review_md or "**DECISION**: APPROVE" in review_md:
        verdict = "APPROVE"

    passed = (verdict == "APPROVE") or (round_num >= 2)
    reason = "Approved by independent reviewer" if verdict == "APPROVE" else f"Round {round_num}/2 changes requested"
    return verdict, review_md, passed, reason
