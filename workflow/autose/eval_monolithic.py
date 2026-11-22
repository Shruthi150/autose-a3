"""Experiment 1 (ADR-001): Monolithic single-agent baseline evaluated against hidden tests."""
from __future__ import annotations

import shutil
from pathlib import Path

from .config import load_config
from .llm import call_gemini, set_token_hook
from .stages import EDIT_RE, _apply_search_replace
from .tools import compile_check, run_cmd, run_tests

TARGET_BY_ISSUE = {
    1: ("tinydb/table.py", "test_issue1_remove_duplicate_ids.py"),
    2: ("tinydb/queries.py", "test_issue2_one_of_iterators.py"),
    3: ("tinydb/table.py", "test_issue3_upsert_multiple.py"),
    4: ("tinydb/queries.py", "test_issue4_startswith_endswith.py"),
    5: ("tinydb/operations.py", "test_issue5_increment_missing_field.py"),
}


def run_monolithic(repo_root: Path, hidden_dir: Path) -> None:
    cfg = load_config()
    model = cfg["models"]["implementer"]
    print("issue,builds,existing_tests_pass,hidden_tests_summary,tokens")

    for num, (target_file, hidden_test) in TARGET_BY_ISSUE.items():
        run_cmd(["git", "checkout", "-q", "--force", "main"], cwd=repo_root)
        run_cmd(["git", "clean", "-fdq", "tests/"], cwd=repo_root)

        issue_md = (repo_root / "experiment" / "issues" / f"issue_{num}.md").read_text(encoding="utf-8")
        src_text = (repo_root / target_file).read_text(encoding="utf-8")

        tok = [0]
        set_token_hook(lambda i, o, t=tok: t.__setitem__(0, t[0] + i + o))

        sys_prompt = """You are a single monolithic coding agent for TinyDB.
Read the issue and directly output SEARCH/REPLACE edit blocks for the source file (no separate spec or design stage):

FILE: tinydb/example.py
<<<<<<< SEARCH
exact existing lines (3-8 lines)
=======
replacement lines
>>>>>>> REPLACE"""
        user_prompt = f"Issue:\n{issue_md}\n\nFile `{target_file}`:\n{src_text}"
        resp = call_gemini(model, sys_prompt, user_prompt)

        edits = EDIT_RE.findall(resp)
        applied = False
        if edits:
            applied = True
            for fname, search, replace in edits:
                fname = fname.strip().strip("`")
                p = repo_root / fname
                if not p.exists():
                    applied = False
                    break
                upd, _ = _apply_search_replace(p.read_text(encoding="utf-8"), search, replace)
                if upd is None:
                    applied = False
                    break
                p.write_text(upd, encoding="utf-8")

        builds = False
        existing_ok = False
        hidden_summary = "skipped (build/edit failed)"
        if applied:
            builds, _ = compile_check(repo_root, [target_file])
            if builds:
                existing_ok, _ = run_tests(repo_root)
                shutil.copy2(hidden_dir / "conftest.py", repo_root / "tests" / "conftest.py")
                shutil.copy2(hidden_dir / hidden_test, repo_root / "tests" / hidden_test)
                h_ok, h_out = run_tests(repo_root, f"tests/{hidden_test}")
                last_line = [ln.strip() for ln in h_out.splitlines() if ln.strip()][-1]
                hidden_summary = f"{'PASS' if h_ok else 'FAIL'} ({last_line})"
                run_cmd(["git", "clean", "-fdq", "tests/"], cwd=repo_root)
                run_cmd(["git", "checkout", "-q", "--", "tests/"], cwd=repo_root)

        print(f"issue-{num},{builds},{existing_ok},{hidden_summary},{tok[0]}", flush=True)


if __name__ == "__main__":
    run_monolithic(
        Path(r"C:\Users\Shruthi.Bathini\.gemini\antigravity\scratch\tinydb_eval"),
        Path(r"C:\Users\Shruthi.Bathini\Desktop\Autonomous Software Engineering\Assignment 3\autose_a3_handoff\local_only\hidden_tests"),
    )
