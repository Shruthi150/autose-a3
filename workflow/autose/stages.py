"""Stages and programmatic gate checks for the 6 SDLC steps.

Each run_stageN returns the artifact plus a pass/fail verdict decided by code
(regex, compiler, pytest, gh exit code), never by the LLM itself (ADR-007).
"""
from __future__ import annotations

import re
from pathlib import Path

from .config import spec_skill
from .ghub import open_pull_request, trigger_and_wait_ci
from .llm import call_gemini
from .security import wrap_untrusted
from .tools import compile_check, run_cmd, run_tests

CODE_RE = re.compile(r"```python\s*(.*?)\s*```", re.DOTALL)
EDIT_RE = re.compile(
    r"FILE:\s*(\S+)\s*\n<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE",
    re.DOTALL,
)


# ----------------- STAGE 1: REQUIREMENTS -----------------
def run_stage1_requirements(issue_title: str, issue_body: str, model: str) -> tuple[str, bool, str]:
    skill_text = spec_skill()
    skill_block = f"\n\nFollow your specification skill:\n{skill_text}\n" if skill_text else ""
    sys_prompt = f"""You are the Requirements Agent in an autonomous SDLC pipeline for TinyDB.
Turn the untrusted issue into spec.md.{skill_block}
Rules:
1. Summarise the problem, expectations and edge cases. If the issue is vague, state your assumptions explicitly.
2. Give a numbered list of testable Acceptance Criteria named AC-1, AC-2, ... Each one must be checkable by a deterministic unit test.
3. Add a section '## Public API' with the exact names, signatures and return values that a test must call.
4. Do NOT write code."""
    user_prompt = f"{wrap_untrusted('issue_title', issue_title)}\n\n{wrap_untrusted('issue_body', issue_body)}"
    spec_md = call_gemini(model, sys_prompt, user_prompt)
    n_ac = len(set(re.findall(r"AC-\d+", spec_md)))
    ok = n_ac >= 2 and "Public API" in spec_md
    return spec_md, ok, f"{n_ac} acceptance criteria, Public API section {'present' if 'Public API' in spec_md else 'missing'}"


# ----------------- STAGE 2: DESIGN -----------------
def run_stage2_design(
    spec_md: str,
    repo_root: str | Path,
    model: str,
    feedback: str = "",
) -> tuple[str, bool, str]:
    sys_prompt = """You are the Design Agent in an autonomous SDLC pipeline for TinyDB.
Plan the change from spec.md and the architecture notes.
Rules:
1. List every source file to edit, each as exactly:
- File: `tinydb/<name>.py`
  - Function: `<name>`
  - Changes: <what changes and why>
2. Only list files under tinydb/. Never list test files.
3. State backward-compatibility impact and edge cases."""
    arch_path = Path(repo_root) / "ARCHITECTURE.md"
    arch = (
        arch_path.read_text(encoding="utf-8")[:24000]
        if arch_path.exists()
        else "tinydb/table.py: Table. tinydb/queries.py: Query. tinydb/operations.py: update ops."
    )
    user_prompt = f"Architecture:\n{arch}\n\nSpecification:\n{spec_md}"
    if feedback:
        user_prompt += f"\n\nPREVIOUS APPROACH FEEDBACK (adjust the design):\n{feedback[-3000:]}"
    design_md = call_gemini(model, sys_prompt, user_prompt)
    files = design_files(design_md, repo_root)
    funcs = re.findall(r"-\s*Function:\s*[`\"]?([A-Za-z0-9_\.]+)[`\"]?", design_md)
    ok = bool(files and funcs)
    return design_md, ok, f"files={files} functions={funcs}"


def design_files(design_md: str, repo_root: str | Path) -> list[str]:
    found = re.findall(r"-\s*File:\s*[`\"]?([A-Za-z0-9_\-\./\\]+\.py)[`\"]?", design_md)
    out: list[str] = []
    for f in found:
        f = f.replace("\\", "/")
        if f.startswith("tinydb/") and "test" not in f and (Path(repo_root) / f).exists() and f not in out:
            out.append(f)
    return out


# ----------------- STAGE 3: IMPLEMENTATION -----------------
def run_stage3_implementation(
    design_md: str,
    repo_root: str | Path,
    target_files: list[str],
    feedback: str,
    model: str,
) -> tuple[str, bool, str]:
    run_cmd(["git", "checkout", "--"] + target_files, cwd=repo_root)  # always edit from clean base
    sources = "\n\n".join(
        f"=== {f} ===\n{(Path(repo_root) / f).read_text(encoding='utf-8')}" for f in target_files
    )
    sys_prompt = """You are the Implementation Agent in an autonomous SDLC pipeline for TinyDB.
Change the code as the design says. Do NOT rewrite whole files. Output ONLY edit blocks:

FILE: tinydb/example.py
<<<<<<< SEARCH
exact existing lines, character for character, with enough context to be unique
=======
replacement lines
>>>>>>> REPLACE

Use as many blocks as needed. Do not write tests. Keep public behaviour backward compatible."""
    user_prompt = f"Design Plan:\n{design_md}\n\nCurrent source files:\n{sources}"
    if feedback:
        user_prompt += f"\n\nTHE PREVIOUS ATTEMPT FAILED WITH:\n{feedback[-4000:]}"
    resp = call_gemini(model, sys_prompt, user_prompt)

    edits = EDIT_RE.findall(resp)
    if not edits:
        return "", False, "Implementer produced no valid SEARCH/REPLACE blocks."
    for fname, search, replace in edits:
        fname = fname.strip().strip("`")
        if fname not in target_files:
            return "", False, f"Edit targets {fname}, which the design did not list."
        path = Path(repo_root) / fname
        text = path.read_text(encoding="utf-8")
        n = text.count(search)
        if n != 1:
            return "", False, f"SEARCH block for {fname} matched {n} times (need exactly 1):\n{search[:300]}"
        path.write_text(text.replace(search, replace), encoding="utf-8")

    ok, msg = compile_check(repo_root, target_files)
    if ok:
        rc, _, err = run_cmd(["python", "-c", "import tinydb"], cwd=repo_root)
        ok, msg = rc == 0, (err or "builds")
    diff = run_cmd(["git", "diff", "--", "tinydb"], cwd=repo_root)[1] if ok else ""
    if ok and not diff.strip():
        return "", False, "Diff is empty; no code was changed."
    return diff, ok, msg


# ----------------- STAGE 4: TESTING -----------------
def run_stage4_testing(
    spec_md: str,
    repo_root: str | Path,
    test_rel_file: str,
    model: str,
    feedback: str = "",
) -> tuple[str, bool, str]:
    sys_prompt = """You are the Testing Agent in an autonomous SDLC pipeline for TinyDB.
Write pytest tests, one or more per Acceptance Criterion in spec.md, using only the Public API in the spec.
Import from tinydb (TinyDB, Query, where, tinydb.operations, tinydb.storages.MemoryStorage).
Return the COMPLETE test file in one ```python block."""
    user_prompt = f"Specification:\n{spec_md}"
    if feedback:
        user_prompt += (
            "\n\nThe previous run printed the output below. If a test itself contradicts the spec, fix the test. "
            f"Never weaken a correct test to make it pass:\n{feedback[-4000:]}"
        )
    resp = call_gemini(model, sys_prompt, user_prompt)
    m = CODE_RE.search(resp)
    test_path = Path(repo_root) / test_rel_file
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(m.group(1) if m else resp, encoding="utf-8")

    new_ok, new_out = run_tests(repo_root, test_rel_file)
    all_ok, all_out = run_tests(repo_root)  # regression gate: existing + new
    passed = new_ok and all_ok
    output = f"--- new tests ---\n{new_out}\n--- full suite ---\n{all_out}"
    report = f"# Test report\n\n**Status**: {'PASSED' if passed else 'FAILED'}\n\n```\n{output[-12000:]}\n```"
    return report, passed, output


# ----------------- STAGE 5: RELEASE -----------------
def run_stage5_release(
    repo_root: str | Path,
    branch: str,
    base_branch: str,
    issue_number: int,
    spec_md: str,
    test_report_md: str,
    commit_msg: str | None = None,
) -> tuple[int, str, str, bool, str]:
    run_cmd(["git", "config", "user.name", "autose-bot"], cwd=repo_root)
    run_cmd(["git", "config", "user.email", "autose-bot@users.noreply.github.com"], cwd=repo_root)
    run_cmd(["git", "add", "tinydb", "tests"], cwd=repo_root)  # never stage .autose/ or workflow files
    rc_diff, _, _ = run_cmd(["git", "diff", "--cached", "--quiet"], cwd=repo_root)
    if rc_diff != 0:
        msg = commit_msg or f"AutoSE: fix for issue #{issue_number}"
        rc_c, out_c, err_c = run_cmd(["git", "commit", "-m", msg], cwd=repo_root)
        if rc_c != 0:
            return 0, "", f"# Release failed\nCommit error: {err_c}\n{out_c}", False, err_c

    # Push uses default env? No, actions/checkout stores auth in .git/config, so scrubbed_env works
    rc_p, out_p, err_p = run_cmd(["git", "push", "-u", "origin", branch, "--force"], cwd=repo_root)
    if rc_p != 0:
        return 0, "", f"# Release failed\nPush error: {err_p}\n{out_p}", False, err_p

    title = f"[AutoSE] Fix for issue #{issue_number}"
    body = (
        f"Closes #{issue_number}\n\n"
        f"## Specification Summary\n{spec_md[:1500]}\n\n"
        "## Verification\nAll new and existing tests passed locally. "
        "See `spec.md`, `design.md`, `diff.patch`, and `test_report.md` in the workflow artifacts.\n\n"
        "_Automated PR — a human maintainer makes the final merge decision._"
    )
    ok, pr_num, pr_url = open_pull_request(repo_root, branch, base_branch, issue_number, title, body)
    if not ok:
        return 0, "", f"# Release failed\nPR creation error: {pr_url}", False, pr_url

    ci_ok, ci_msg = trigger_and_wait_ci(repo_root, branch)
    pr_md = (
        f"# Pull Request\n\n"
        f"- **PR**: #{pr_num} ({pr_url})\n"
        f"- **Branch**: `{branch}` -> `{base_branch}`\n"
        f"- **CI Status**: {'PASSED' if ci_ok else 'FAILED'} ({ci_msg})\n"
    )
    return pr_num, pr_url, pr_md, (ok and ci_ok), ci_msg


# ----------------- STAGE 6: INDEPENDENT REVIEW -----------------
def run_stage6_review(
    issue_title: str,
    issue_body: str,
    diff_patch: str,
    model: str,
    round_num: int,
    pytest_output: str = "",
    shared_context: str = "",
) -> tuple[str, str, str, bool, str]:
    """Independent adversarial review.

    In normal mode (shared_context == ''), the reviewer ONLY receives the issue,
    the PR diff, and its own pytest execution output. Never the implementer's
    conversation, spec, or design.
    """
    if shared_context:
        # Experiment 2 variant (ADR-008): non-independent reviewer with implementer context
        sys_prompt = """You are a code reviewer. Review the pull request using the implementer's spec, design, and diff.
Put one verdict on its own line:
DECISION: APPROVE
or
DECISION: REQUEST_CHANGES
And on the next line:
CATEGORY: NONE (if APPROVE) or CODE or APPROACH."""
        user_prompt = (
            f"{wrap_untrusted('issue_title', issue_title)}\n\n"
            f"{wrap_untrusted('issue_body', issue_body)}\n\n"
            f"<implementer_context>\n{shared_context[:6000]}\n</implementer_context>\n\n"
            f"<pull_request_diff>\n{diff_patch}\n</pull_request_diff>"
        )
    else:
        sys_prompt = """You are an independent, sceptical senior code reviewer. You did not write this change and have no knowledge of the implementer's reasoning.
Inspect the diff against the original issue and look actively for:
1. Requirements the diff misses or handles only partially.
2. Edge cases: duplicate inputs, non-string values, missing keys, one-shot iterators/generators, empty inputs.
3. Silent regressions, swallowed exceptions (e.g., blanket except), non-atomic multi-write loops when single write is required.
4. Missing or weak unit tests.

Approve ONLY if you can name no real defect.
Put your verdict on its own line:
DECISION: APPROVE
or
DECISION: REQUEST_CHANGES
On the next line put:
CATEGORY: NONE
or
CATEGORY: CODE
or
CATEGORY: APPROACH
Then list concrete findings."""
        test_block = f"\n\n<reviewer_pytest_run>\n{pytest_output[-3000:]}\n</reviewer_pytest_run>" if pytest_output else ""
        user_prompt = (
            f"{wrap_untrusted('issue_title', issue_title)}\n\n"
            f"{wrap_untrusted('issue_body', issue_body)}\n\n"
            f"<pull_request_diff>\n{diff_patch}\n</pull_request_diff>{test_block}"
        )

    review_md = call_gemini(model, sys_prompt, user_prompt)
    verdict = (
        "APPROVE"
        if re.search(r"^\s*\**DECISION:?\**:?\s*APPROVE\b", review_md, re.M)
        else "REQUEST_CHANGES"
    )
    cat_m = re.search(r"^\s*\**CATEGORY:?\**:?\s*(APPROACH|CODE|NONE)\b", review_md, re.M)
    category = cat_m.group(1) if cat_m else ("NONE" if verdict == "APPROVE" else "CODE")
    done = verdict == "APPROVE" or round_num >= 2
    return verdict, category, review_md, done, f"round {round_num}/2, verdict={verdict}, category={category}"
