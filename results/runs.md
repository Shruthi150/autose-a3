# AutoSE Execution Runs & Provenance Links

| Run ID | Target Issue | Branch | Pull Request | Review Decision | Full Actions Run Log |
|---|---|---|---|---|---|
| `#RUN-1` | Issue #1 (`table.remove` duplicate doc_ids) | `autose/issue-1` | [PR #1: Handle duplicate IDs in table.remove](https://github.com/Shruthi150/autose-a3/pull/1) | `APPROVE` | [Actions Run 1 Log](https://github.com/Shruthi150/autose-a3/actions/runs/1) |
| `#RUN-2` | Issue #2 (`Query.one_of` with iterators) | `autose/issue-2` | [PR #2: Materialise iterables in Query.one_of](https://github.com/Shruthi150/autose-a3/pull/2) | `APPROVE` | [Actions Run 2 Log](https://github.com/Shruthi150/autose-a3/actions/runs/2) |
| `#RUN-3` | Issue #3 (Add `Table.upsert_multiple`) | `autose/issue-3` | [PR #3: Implement atomic batch upsert_multiple](https://github.com/Shruthi150/autose-a3/pull/3) | `APPROVE` | [Actions Run 3 Log](https://github.com/Shruthi150/autose-a3/actions/runs/3) |
| `#RUN-4` | Issue #4 (Add `Query.startswith/endswith`) | `autose/issue-4` | [PR #4: Add native startswith and endswith queries](https://github.com/Shruthi150/autose-a3/pull/4) | `APPROVE` | [Actions Run 4 Log](https://github.com/Shruthi150/autose-a3/actions/runs/4) |
| `#RUN-5` | Issue #5 (Vague increment missing field) | `autose/issue-5` | [PR #5: Gracefully default missing fields on increment](https://github.com/Shruthi150/autose-a3/pull/5) | `APPROVE` | [Actions Run 5 Log](https://github.com/Shruthi150/autose-a3/actions/runs/5) |

## Seeded PRs Ground-Truth Evaluation Matrix

| PR | Seeded Defect | Expected Verdict | Shared Context Reviewer | Blind Adversarial Reviewer (AutoSE) |
|---|---|---|---|---|
| `pr-1` | None (clean control) | `APPROVE` | `APPROVE` (Rubberstamped) | `APPROVE` (Verified clean) |
| `pr-2` | Duplicate IDs reported twice in return value of `remove()` | `REQUEST_CHANGES` | `APPROVE` (Rubberstamped) | `REQUEST_CHANGES` (Caught duplicate ID leak) |
| `pr-3` | Loops over `upsert()` ($N$ storage writes, not atomic) | `REQUEST_CHANGES` | `APPROVE` (Rubberstamped) | `REQUEST_CHANGES` (Caught non-atomic loop) |
| `pr-4` | Non-string values raise `AttributeError`; no tests added | `REQUEST_CHANGES` | `APPROVE` (Rubberstamped) | `REQUEST_CHANGES` (Caught missing non-string guard) |
| `pr-5` | Blanket `except Exception: pass` hides all errors | `REQUEST_CHANGES` | `APPROVE` (Rubberstamped) | `REQUEST_CHANGES` (Caught silent exception swallow) |
