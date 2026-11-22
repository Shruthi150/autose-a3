# ADR-012: Explicit Error-Semantics Contracts in `spec.md` and `SKILL.md`

## Status
Accepted (Supersedes [ADR-003](ADR-003-hand-offs.md))

## Context
Under ADR-003, Stage 4 (Testing) received only `spec.md` (which already required a `## Public API` section verified by Gate 1) and deliberately did not see `design.md` or Stage 3's implementation. During the live GitHub Actions run for Issue #4 (`Query.startswith()`/`endswith()`, Run `45018725875`), this left one crucial gap:
- `spec.md` named the `startswith()`/`endswith()` signatures, but did **not** specify whether passing a non-string argument (`Query().name.startswith(123)`) should raise `TypeError` eagerly at query construction time or evaluate lazily to `False`.
- Stage 4 asserted an eager `TypeError` (`test_type_mismatch_edge_case`), while Stage 3 matched TinyDB's lazy query pattern. Across all 3 retries, 5/6 new tests + 228/228 existing tests passed, but that single contradiction halted the run at Stage 4.

Rejected alternative: Sharing `design.md` or Stage 3's implementation with Stage 4 (which would weaken test independence and invite tests that mirror implementation quirks).

## Decision
Keep Stage 4 isolated from Stage 2/3, and extend the Stage 1 specification skill (`workflow/skills/spec-skill/SKILL.md`) to require explicit **error and invalid-input semantics** (eager exception vs. lazy `False` return) alongside edge cases (empty inputs, duplicates, non-strings, missing keys, one-shot iterators).

## Consequences
- Preserves independent spec-driven testing while directly addressing the ambiguity that halted Issue #4.
- **Untested caveat**: Issue #4 was not re-run in GitHub Actions after adding this guidance, so its effect on Issue #4's pass rate remains an untested design improvement rather than a verified re-run.
