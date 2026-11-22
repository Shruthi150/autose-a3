# ADR-012: Explicit `Public API` and Error-Semantics Contracts in `spec.md`

## Status
Accepted (Supersedes [ADR-003](ADR-003-hand-offs.md))

## Context
Under ADR-003, Stage 4 (Testing) received only `spec.md` and deliberately did not see `design.md` or Stage 3's implementation. During the live GitHub Actions run for Issue #4 (`Query.startswith()`/`endswith()`, Run `45018725875`), this information hiding caused a deadlock:
- Stage 4 wrote `test_type_mismatch_edge_case` asserting that `Query().name.startswith(123)` raises `TypeError` eagerly at query construction time.
- Stage 3 implemented `startswith()` lazily (matching TinyDB's `matches()`/`search()`), returning a `QueryInstance` that evaluates to `False` on non-strings.
- Across all 3 attempts, 5/6 new tests + 228/228 existing tests passed, but that single disagreement halted the run at Stage 4.

## Decision
We keep Stage 4 isolated from Stage 2/3 (preserving test independence), but tighten the Stage 1 (`spec.md`) hand-off contract:
1. `spec.md` MUST include a `## Public API` section (enforced by Gate 1) specifying exact method signatures, return types, and invalid-input/error semantics (eager exception vs. lazy `False`).
2. `workflow/skills/spec-skill/SKILL.md` explicitly prompts Stage 1 to state assumptions on edge cases (empty inputs, duplicates, non-strings, missing keys, one-shot iterators).

## Consequences
- Preserves anti-sycophancy test independence while reducing spec-ambiguity deadlocks between Stage 3 and Stage 4.
- Adds slightly stricter formatting requirements to `spec.md`, enforced deterministically at Gate 1.
