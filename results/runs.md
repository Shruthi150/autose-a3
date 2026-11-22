# Workflow Runs, Pull Requests, and Reviews

All runs below are real GitHub Actions executions on `Shruthi150/autose-a3` (pinned copy/import of TinyDB `edff96a`).

## Final Main Pipeline Runs (Issues #1–#5)

| Issue | Type | Branch / Commit | Actions Run | Pull Request | Final State | Stage 6 Verdict | Hidden Tests (Cases / Funcs) |
|---|---|---|---|---|---|---|---|
| **#1** `table.remove` dup `doc_ids` | Bug | `autose/issue-1` (`79f6035`) | [Run 45017452563](https://github.com/Shruthi150/autose-a3/actions/runs/45017452563) | [PR #6](https://github.com/Shruthi150/autose-a3/pull/6) | Complete (Stages 1–6) | `APPROVE` | **8 / 8** (4 funcs) |
| **#2** `Query.one_of` iterators | Bug | `autose/issue-2` (`1fcfdc0`) | [Run 45017663476](https://github.com/Shruthi150/autose-a3/actions/runs/45017663476) | [PR #7](https://github.com/Shruthi150/autose-a3/pull/7) | Complete (Stages 1–6) | `APPROVE` | **14 / 14** (4 funcs) |
| **#3** `Table.upsert_multiple` | Feature | `autose/issue-3` (`88cae7e`) | [Run 45017875028](https://github.com/Shruthi150/autose-a3/actions/runs/45017875028) | [PR #8](https://github.com/Shruthi150/autose-a3/pull/8) | `rework_round_1` halted on 1 failing test; `review_round_2` skipped; handed to human | `REQUEST_CHANGES` | **5 / 9** (5 funcs) |
| **#4** `Query.startswith/endswith` | Feature | *(No PR opened)* | [Run 45018725875](https://github.com/Shruthi150/autose-a3/actions/runs/45018725875) | None (Gate 4 halted after 3 attempts) | Halted at Stage 4 (`FAILED.md`) | N/A | **0 / 8** (4 funcs, no PR) |
| **#5** `increment` missing field | Vague | `autose/issue-5` (`2bfcf29`) | [Run 45019273789](https://github.com/Shruthi150/autose-a3/actions/runs/45019273789) | [PR #9](https://github.com/Shruthi150/autose-a3/pull/9) | Complete (Stages 1–6) | `APPROVE` | **12 / 12** (4 funcs) |

## Earlier Diagnostic / Failed Runs (Led to Engineering Fixes)

| Run | Target | Failure Observed | Root Cause & Fix Applied |
|---|---|---|---|
| [Run 45016202025](https://github.com/Shruthi150/autose-a3/actions/runs/45016202025) | Issue #1 | Stage 3 failed attempts 2–3 (`SEARCH block matched 0 times`) | Model re-wrapped a comment line inside `SEARCH`. Added code-weighted fuzzy line-window matcher (`abc1499`). |
| [Run 45017056626](https://github.com/Shruthi150/autose-a3/actions/runs/45017056626) | Issue #1 | Stage 5 reported `CI action_required` even though dispatched `AutoSE PR CI #3` passed | `gh run list` picked up duplicate `pull_request: synchronize` event instead of `workflow_dispatch`. Filtered by `--event workflow_dispatch` and new `databaseId` (`0984c67`). |

## Decision Experiment 2: Seeded PRs (`experiment/seeded_prs/`)

Executed locally via `python -m workflow.autose.eval_seeded` with `gemini-3.1-flash-lite` (diff-only, 1 run per cell, 11,435 measured tokens across both variants). Full Experiment 1 (monolithic) and Experiment 2 rows are in [`results/results.csv`](results.csv).

| Seeded PR | Planted Flaw (`labels.csv`) | Expected | Blind Independent (ADR-008) | Shared Context (Canned Note) | Tokens (both variants) |
|---|---|---|---|---|---|
| `pr-1` | None (correct control) | `APPROVE` | `APPROVE` (Match) | `APPROVE` (Match) | 2,427 |
| `pr-2` | Duplicate IDs reported twice in `remove()` return | `REQUEST_CHANGES` | `REQUEST_CHANGES` (Match) | `APPROVE` (**Missed**) | 2,415 |
| `pr-3` | Loops over `upsert()`: $N$ writes, not atomic | `REQUEST_CHANGES` | `REQUEST_CHANGES` (Match) | `REQUEST_CHANGES` (Match) | 2,649 |
| `pr-4` | `AttributeError` on non-strings; no tests added | `REQUEST_CHANGES` | `REQUEST_CHANGES` (Match) | `REQUEST_CHANGES` (Match) | 1,919 |
| `pr-5` | Blanket `except Exception: pass` hides errors | `REQUEST_CHANGES` | `REQUEST_CHANGES` (Match) | `REQUEST_CHANGES` (Match) | 2,025 |
| **Total** | **1 clean + 4 defective** | **5 / 5** | **4/4 defective flagged, 1/1 clean approved (5/5)** | **3/4 defective flagged, 1/1 clean approved (4/5)** | **11,435** |
