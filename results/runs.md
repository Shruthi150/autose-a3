# Workflow Runs, Pull Requests, and Reviews

All runs below are real GitHub Actions executions on `Shruthi150/autose-a3` (pinned TinyDB `edff96a`).

## Main Pipeline Runs (Issues #1–#5)

| Issue | Type | Branch / Commit | Actions Run | Pull Request | Stage Reached | Stage 6 Reviewer Verdict | Hidden Acceptance Tests |
|---|---|---|---|---|---|---|---|
| **#1** `table.remove` dup `doc_ids` | Bug | `autose/issue-1` (`79f6035`) | [Run 45017452563](https://github.com/Shruthi150/autose-a3/actions/runs/45017452563) | [PR #6](https://github.com/Shruthi150/autose-a3/pull/6) | Stage 6 (Complete) | `APPROVE` | **8 / 8 PASS (100%)** |
| **#2** `Query.one_of` iterators | Bug | `autose/issue-2` (`1fcfdc0`) | [Run 45017663476](https://github.com/Shruthi150/autose-a3/actions/runs/45017663476) | [PR #7](https://github.com/Shruthi150/autose-a3/pull/7) | Stage 6 (Complete) | `APPROVE` | **14 / 14 PASS (100%)** |
| **#3** `Table.upsert_multiple` | Feature | `autose/issue-3` (`88cae7e`) | [Run 45017875028](https://github.com/Shruthi150/autose-a3/actions/runs/45017875028) | [PR #8](https://github.com/Shruthi150/autose-a3/pull/8) | Stage 6 $\rightarrow$ `rework_round_1` halted at test | `REQUEST_CHANGES` | **5 / 9 PASS (55.6%)** |
| **#4** `Query.startswith/endswith` | Feature | *(No PR opened)* | [Run 45018725875](https://github.com/Shruthi150/autose-a3/actions/runs/45018725875) | None (Gate 4 halted after 3 attempts) | Stage 4 (Halted cleanly) | N/A | **0 / 8 (No PR)** |
| **#5** `increment` missing field | Vague | `autose/issue-5` (`2bfcf29`) | [Run 45019273789](https://github.com/Shruthi150/autose-a3/actions/runs/45019273789) | [PR #9](https://github.com/Shruthi150/autose-a3/pull/9) | Stage 6 (Complete) | `APPROVE` | **12 / 12 PASS (100%)** |

## Decision Experiment 2: Seeded PRs (`experiment/seeded_prs/`)

Executed with `python -m workflow.autose.eval_seeded` using `gemini-3.1-flash-lite` (11,435 total tokens):

| Seeded PR | Planted Flaw (`labels.csv`) | Expected | Blind Independent Reviewer (ADR-008) | Shared-Context Reviewer | Tokens |
|---|---|---|---|---|---|
| `pr-1` | None (correct control) | `APPROVE` | `APPROVE` (Match) | `APPROVE` (Match) | 2,427 |
| `pr-2` | Duplicate IDs reported twice in `remove()` return | `REQUEST_CHANGES` | `REQUEST_CHANGES` (Match) | `APPROVE` (**Missed / Rubber-stamped**) | 2,415 |
| `pr-3` | Loops over `upsert()`: $N$ writes, not atomic | `REQUEST_CHANGES` | `REQUEST_CHANGES` (Match) | `REQUEST_CHANGES` (Match) | 2,649 |
| `pr-4` | `AttributeError` on non-strings; no tests added | `REQUEST_CHANGES` | `REQUEST_CHANGES` (Match) | `REQUEST_CHANGES` (Match) | 1,919 |
| `pr-5` | Blanket `except Exception: pass` hides errors | `REQUEST_CHANGES` | `REQUEST_CHANGES` (Match) | `REQUEST_CHANGES` (Match) | 2,025 |
| **Accuracy** | | | **5 / 5 (100%)** | **4 / 5 (80%)** | **11,435** |
