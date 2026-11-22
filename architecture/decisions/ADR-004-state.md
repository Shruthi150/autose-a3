# ADR-004: Dual-Layer State Persistence (Artifacts + PR Branch)

## Status
Accepted

## Context
State must survive across GitHub Actions jobs (`implement_and_release` $\rightarrow$ `review_round_1` $\rightarrow$ `rework_round_1` $\rightarrow$ `review_round_2`), remain inspectable by humans, and never pollute the PR's git diff with scratchpads.

## Decision
We store state in two clean layers:
1. **PR Branch (`autose/issue-N`)**: Holds ONLY code changes under `tinydb/` and tests under `tests/test_autose_issue_N.py` (`git add tinydb tests`).
2. **GitHub Workflow Artifacts (`.autose/artifacts/`)**: Holds `spec.md`, `design.md`, `diff.patch`, `test_report.md`, `pr.md`, `review.md`, `FAILED.md`, and `state.json` (recording stage statuses, attempts, and exact token usage), uploaded with `if: always()` and 30-day retention.

If a run is restarted for the same issue, `git checkout -B autose/issue-N` resets the branch cleanly and `open_pull_request()` reuses any existing open PR instead of failing.

## Consequences
- Clean git history and clean PR diffs.
- Full traceability of every stage artifact and token count per run.
- Rework jobs download prior artifacts cleanly via `actions/download-artifact@v4`.
