# ADR-002: Hybrid Control Flow (Python State Machine Inside Multi-Job GitHub Actions)

## Status
Accepted

## Context
We must coordinate six stages, enforce quality gates, handle bounded implementation-test retries (up to 3), and enforce a separate read-only reviewer that can trigger up to 2 review rounds.

Options considered:
1. **Six separate GitHub Actions jobs** with artifact hand-offs between every stage (high runner spin-up latency for every test retry).
2. **Single monolithic GitHub Actions job** running all 6 stages (cannot enforce GitHub-level read-only permissions on the reviewer).
3. **Hybrid: Python FSM for Stages 1–5 inside Job 1, plus separate GitHub Actions jobs for Review Round 1, Conditional Rework, and Review Round 2.**

## Decision
We choose **Option 3 (Hybrid Control Flow)**.
- Inside `implement_and_release`, `workflow/autose/cli.py` deterministically drives Stages 1–5 and loops Stage 3 $\leftrightarrow$ Stage 4 up to 3 attempts on failure without runner startup overhead.
- Between Release and Review, GitHub Actions job boundaries (`review_round_1` $\rightarrow$ `rework_round_1` $\rightarrow$ `review_round_2`) enforce strict isolation and cap review loops at 2 rounds.
- Routing on `REQUEST_CHANGES` is determined by the reviewer's structured `CATEGORY` (`APPROACH` returns to Stage 2 Design; `CODE` returns to Stage 3 Implementation).

## Consequences
- Fast inner test-fix loop (~10–20s per retry) without provisioning new VMs.
- Reviewer isolation and no-push permissions are enforced by GitHub's job token rather than trust.
- A runner crash inside Job 1 restarts Stages 1–5 from scratch (mitigated by `if: always()` artifact upload).
