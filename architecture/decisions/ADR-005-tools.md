# ADR-005: Role-Based Tooling and Principle of Least Privilege

## Status
Accepted

## Context
Granting arbitrary shell access or broad `GITHUB_TOKEN` permissions to LLM agents creates security and reliability risks (secret leakage, accidental pushes, editing workflow files).

Rejected alternative: Giving LLM agents an unrestricted bash/shell execution tool and sharing write permissions across all stages.

## Decision
We enforce least privilege at both the Python and GitHub Actions layers:
- **No free-form shell tool for LLMs**: Agents emit structured outputs (Markdown specs/designs, `SEARCH/REPLACE` edit blocks, Python test files). Deterministic Python code in `tools.py` applies edits, validates paths (only `tinydb/*.py` listed by Design), and runs `py_compile` and `pytest`.
- **Scrubbed subprocess environment (`security.py`)**: All agent-triggered subprocesses run with `scrubbed_env()`, stripping `GEMINI_API_KEY` and `GITHUB_TOKEN` so test code or untrusted inputs cannot read secrets.
- **Job-level GitHub permissions**:
  - `implement_and_release` & `rework_round_1`: `contents: write`, `pull-requests: write`, `issues: write`, `actions: write`.
  - `review_round_1` & `review_round_2`: `contents: read`, `pull-requests: write` — physically incapable of pushing commits or merging.

## Consequences
- Eliminates arbitrary code execution via LLM shell tools and prevents secret exfiltration.
- Edit blocks require exact context matching; a mismatch triggers a structured retry with feedback.
