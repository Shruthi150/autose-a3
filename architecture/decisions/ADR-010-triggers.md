# ADR-010: Workflow Triggers, PR-Comment Filtering, and Queued Concurrency Control

## Status
Accepted

## Context
Workflows must be triggered cleanly when maintainers add a label (`autose`) or post an issue comment (`/autose`), without racing when multiple events arrive on the same issue or accidentally firing on PR comments.

Rejected alternative: Unserialized triggers (allowing parallel runs to race on the same `autose/issue-N` branch) or `cancel-in-progress: true` (which could kill an in-flight `git push` mid-run if a label and `/autose` comment arrive back-to-back).

## Decision
We implement a dual-trigger filter with queued per-issue concurrency:
```yaml
concurrency:
  group: autose-issue-${{ github.event.issue.number }}
  cancel-in-progress: false
```
1. **Trigger filter**: `issues: [labeled]` (`autose`) OR `issue_comment: [created]` starting with `/autose` AND `!github.event.issue.pull_request` (explicitly ignoring `/autose` comments on open PRs).
2. **Collaborator Authorization Gate**: Calls `gh api repos/$REPO/collaborators/$ACTOR/permission` and aborts unless the actor has `admin`, `maintain`, or `write` permission.
3. **Queued concurrency**: `cancel-in-progress: false` ensures a second trigger on the same issue waits for the active run to finish instead of interrupting a git push.

## Consequences
- Prevents split-brain branch collisions and half-pushed commits on simultaneous triggers.
- Shields repository tokens and free-tier API quota from unprivileged public users.
