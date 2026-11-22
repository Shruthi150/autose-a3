# ADR-003: Contract-Based Hand-offs and Deliberate Information Hiding

## Status
Accepted

## Context
Passing full conversation histories across stages causes context bloat, higher token cost, and confirmation bias (especially in testing and review).

## Decision
Each stage receives only a minimal, explicit contract:
- **Stage 1 $\rightarrow$ Stage 2**: `spec.md` + `ARCHITECTURE.md` (withheld: raw user metadata).
- **Stage 2 $\rightarrow$ Stage 3**: `design.md` + exact target `tinydb/*.py` files + prior failure traceback if retrying (withheld: `spec.md` narrative, unrelated modules).
- **Stage 3 $\rightarrow$ Stage 4**: `spec.md` only + workspace code on disk (deliberately withheld: `design.md` and implementer reasoning, so tests verify requirements rather than mirroring implementation quirks).
- **Stage 5 $\rightarrow$ Stage 6**: Original issue title/body, `git diff origin/<base>...HEAD`, and the reviewer's own `pytest` output (deliberately withheld: `spec.md`, `design.md`, `test_report.md`, and all implementer logs).

## Consequences
- Reduces prompt tokens and prevents sycophantic self-verification.
- Requires `spec.md` to include an explicit `## Public API` section so Stage 4 knows exact signatures to test.
