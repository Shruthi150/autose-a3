# Decision Experiments: Variants

We empirically test two core architectural decisions:

## Experiment 1: ADR-001 (Work Splitting — Multi-Agent vs. Monolithic)
- **Baseline (`default`)**: 6 specialized stages with isolated contexts (`Requirements` -> `Design` -> `Implementation` -> `Testing` -> `Release` -> `Independent Review`).
- **Variant (`monolithic`)**: A single agent prompt receives the issue and target source file and must emit both the code edit and tests in one turn without separate spec/design/testing agents.
- **Evaluation**: Compare stage pass rates, hidden-test pass rates (`local_only/hidden_tests/`), and total token usage across the 5 TinyDB issues.

## Experiment 2: ADR-008 (Reviewer Independence — Blind vs. Shared Context)
- **Baseline (`blind_independent`)**: Stage 6 reviewer receives ONLY the original issue, the PR diff, and its own `pytest` output, with the sceptical adversarial prompt.
- **Variant (`shared_context`)**: Reviewer receives the implementer's rationale/spec/design alongside the diff, with a neutral review prompt.
- **Evaluation**: Run both reviewer variants on the 5 seeded PRs (`experiment/seeded_prs/pr-1.patch` through `pr-5.patch`) and measure precision/recall against ground-truth `labels.csv`.
