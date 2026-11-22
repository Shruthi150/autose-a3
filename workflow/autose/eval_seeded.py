"""Evaluate Stage 6 Reviewer (blind vs shared_context) on the 5 seeded PRs."""
from __future__ import annotations

import csv
from pathlib import Path

from .config import load_config
from .llm import set_token_hook
from .stages import run_stage6_review


def main() -> None:
    repo = Path(".").resolve()
    cfg = load_config()
    model = cfg["models"]["reviewer"]
    seeded = repo / "experiment" / "seeded_prs"
    issues_dir = repo / "experiment" / "issues"

    rows = list(csv.DictReader((seeded / "labels.csv").open(encoding="utf-8")))
    print("pr,expected,blind_verdict,blind_match,shared_verdict,shared_match,tokens")

    for row in rows:
        pr_id = row["pr"]
        issue_num = row["targets_issue"]
        expected = row["expected_verdict"].upper()
        issue_text = (issues_dir / f"issue_{issue_num}.md").read_text(encoding="utf-8")
        title = issue_text.splitlines()[0].lstrip("# ").strip()
        diff = (seeded / f"{pr_id}.patch").read_text(encoding="utf-8")

        tok = [0]
        set_token_hook(lambda i, o, t=tok: t.__setitem__(0, t[0] + i + o))

        v_blind, _, _, _, _ = run_stage6_review(title, issue_text, diff, model, round_num=1)
        fake_rationale = (
            f"Implementer notes for {pr_id}: I carefully analyzed issue #{issue_num}, "
            "implemented a clean and minimal fix, and verified that all existing TinyDB tests pass."
        )
        v_shared, _, _, _, _ = run_stage6_review(
            title, issue_text, diff, model, round_num=1, shared_context=fake_rationale
        )
        print(f"{pr_id},{expected},{v_blind},{v_blind == expected},{v_shared},{v_shared == expected},{tok[0]}")


if __name__ == "__main__":
    main()
