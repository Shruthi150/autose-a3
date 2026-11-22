# ADR-010: Workflow Triggers, PR-Comment Filtering, and Queued Concurrency Control

## Status
Accepted

## Context
Workflows must be triggered cleanly when maintainers add a label (`autose`) or post an issue comment (`/autose`), without racing when multiple events arrive on the same issue or accidentally firing on PR comments.

Rejected alternative: Unserialized triggers (allowing parallel runs to race on the same `autose/issue-N` branch) or `cancel-in-progress: true` (which could kill an in-flight `git push` mid-run if a label and `/autose` comment arrive back-to-back).

## Decision
We implement a dual-trigger filter with job-level queued per-issue concurrency on `implement_and_release`:
```yaml
concurrency:
  group: autose-issue-${{ github.event.issue.number }}
  cancel-in-progress: false
```
1. **Trigger filter**: `issues: [labeled]` (`autose`) OR `issue_comment: [created]` starting with `/autose` AND `!github.event.issue.pull_request` (explicitly ignoring `/autose` comments on open PRs).
2. **Collaborator Authorization Gate**: Calls `gh api repos/$REPO/collaborators/$ACTOR/permission` *before* checkout or `pip install`, aborting unless the actor has `admin`, `maintain`, or `write` permission.
3. **Job-level queued concurrency**: Placing `concurrency:` on `implement_and_release` (after the `if:` trigger filter) prevents ordinary non-`/autose` comments from occupying the single pending queue slot, and `cancel-in-progress: false` avoids killing an in-flight `git push`.
4. **Branch protection**: `main` and `master` require pull requests before merging (repository admins may bypass for direct docs/workflow maintenance commits, while bot tokens never push to `main`/`master`).

## Consequences
- Prevents split-brain branch collisions and half-pushed commits on simultaneous triggers.
- Shields repository tokens and free-tier API quota from unprivileged public users.
