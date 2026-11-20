# ADR-010: Workflow Triggers and Concurrency Control

## Status
Accepted

## Context
Workflows must be triggered cleanly when maintainers add a label (`autose`) or post an issue comment (`/autose`), without racing when multiple events occur.

## Decision
We implement a dual-trigger filter with GitHub Actions concurrency groups:
```yaml
concurrency:
  group: autose-issue-${{ github.event.issue.number }}
  cancel-in-progress: true
```
We also mandate a Collaborator Authorization Gate ensuring only users with `admin`, `write`, or `maintain` permissions can execute the workflow, preventing unauthorized runs from untrusted public contributors.

## Consequences
- Protects against duplicate runs and split-brain git branches.
- Shields repository tokens and CI compute minutes from public abuse.
