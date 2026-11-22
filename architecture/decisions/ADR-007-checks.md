# ADR-007: Programmatic Quality Gates Over LLM Self-Certification

## Status
Accepted

## Context
LLMs frequently claim their code "works and passes tests" without running a compiler or test runner. Every stage hand-off must be gated by objective, deterministic checks.

Rejected alternative: Relying on LLM self-certification or an LLM-only judge to decide whether code builds or tests pass.

## Decision
No agent can self-certify a stage. External Python code evaluates every gate:
1. **Stage 1 (Requirements)**: Regex checks $\ge 2$ distinct `AC-N` criteria and a `Public API` section in `spec.md`.
2. **Stage 2 (Design)**: Regex checks that at least one existing `tinydb/*.py` file and at least one function name are specified in `design.md`.
3. **Stage 3 (Implementation)**: Unique `SEARCH/REPLACE` match, `python -m py_compile`, `python -c "import tinydb"`, and non-empty `git diff`.
4. **Stage 4 (Testing)**: `python -m pytest -q -p no:cacheprovider -o addopts=` must exit `0` on BOTH the new test file and the full TinyDB test suite. (`-o addopts=` overrides TinyDB's `pytest.ini` coverage flags that otherwise fail when `pytest-cov` is absent.)
5. **Stage 5 (Release)**: `gh pr create` succeeds (or reuses open PR) AND explicitly dispatched `autose-ci.yml` completes with `conclusion == "success"`.
6. **Stage 6 (Review)**: Regex parses `DECISION: APPROVE` or `REQUEST_CHANGES` and `CATEGORY: CODE | APPROACH | NONE`; terminates on `APPROVE` or after 2 review rounds.

## Consequences
- Eliminates hallucinated passes and catches regressions in existing TinyDB tests immediately.
- Requires agents to follow strict formatting (e.g., `FILE:` + `<<<<<<< SEARCH` blocks).
