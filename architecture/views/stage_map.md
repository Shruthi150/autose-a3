# Architecture Stage Map

| # | Stage | Agent / Component | Model | Artifact | Programmatic Check Before Hand-off | Failure / Loop Behaviour |
|---|---|---|---|---|---|---|
| 1 | **Requirements** | `RequirementsAgent` (`stages.py`) + A1 `spec-skill` | `gemini-3.1-flash-lite` | `spec.md` | Regex verifies $\ge 2$ `AC-N` entries and a `Public API` section. | Write `FAILED.md`, upload artifacts, halt run. |
| 2 | **Design** | `DesignAgent` (`stages.py`) + A2 `ARCHITECTURE.md` | `gemini-3.1-flash-lite` | `design.md` | Regex verifies existing `tinydb/*.py` file paths and function names. | Write `FAILED.md`, upload artifacts, halt run. |
| 3 | **Implementation** | `ImplementationAgent` (`stages.py`, SEARCH/REPLACE) | `gemini-3.1-flash-lite` | `diff.patch` | Unique SEARCH match, `py_compile`, `import tinydb`, non-empty diff. | Pass error back to Stage 3 (within 3-attempt budget). |
| 4 | **Testing** | `TestingAgent` (`stages.py`, spec-only) | `gemini-3.1-flash-lite` | `test_report.md` | `pytest -q -o addopts=` exits 0 on both new tests and full suite. | Feed failure output back to Stage 3 & 4 (up to 3 attempts); halt if exhausted. |
| 5 | **Release** | Deterministic `git` + `gh` CLI (`ghub.py`) | None (deterministic) | `pr.md` + PR link | PR is open on GitHub AND dispatched `autose-ci.yml` completes with `success`. | Write `FAILED.md`, upload artifacts, halt run. |
| 6 | **Review** | `IndependentReviewerAgent` (separate read-only job) | `gemini-3.1-flash-lite` (fallback `3.5-flash-lite`) | `review.md` | Reviewer outputs `APPROVE`, or 2 review rounds are used up. | On `REQUEST_CHANGES`: `rework_round_1` routes `APPROACH` $\rightarrow$ Stage 2 or `CODE` $\rightarrow$ Stage 3, then `review_round_2`. |
