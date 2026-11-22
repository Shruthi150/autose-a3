# ADR-008: Enforcing Reviewer Independence and Preventing Rubber-Stamping

## Status
Accepted

## Context
An LLM reviewer that sees the implementer's reasoning, spec, or design tends to agree with the implementer's rationalizations and approve buggy or incomplete PRs.

## Decision
We enforce four concrete independence barriers in Stage 6:
1. **Separate GitHub Actions Job (`review_round_1` / `review_round_2`)**: Runs on a fresh runner checkout of the PR branch, with zero shared memory or conversation state from `implement_and_release`.
2. **Read-Only Code Permissions**: The reviewer job declares `permissions: contents: read, pull-requests: write`. GitHub itself prevents it from pushing commits or merging.
3. **Strict Context Filtering**: The reviewer receives ONLY (a) the original untrusted issue title/body, (b) `git diff origin/<base>...HEAD -- tinydb tests` computed directly from git, and (c) the output of running `pytest` itself. It NEVER sees `spec.md`, `design.md`, `test_report.md`, or implementer logs.
4. **Sceptical Adversarial Prompt**: Instructs the reviewer to actively hunt for missed requirements, edge cases (duplicates, non-strings, one-shot iterators, missing keys), swallowed exceptions, multi-write loops, and weak tests, and to approve only if it can name no real defect.

## Consequences
- Tested empirically against 5 seeded PRs (`experiment/seeded_prs/pr-1..5.patch`) with known ground-truth flaws (`labels.csv`).
- Occasional false positives on valid PRs are handled safely via `rework_round_1` and the 2-round cap.
