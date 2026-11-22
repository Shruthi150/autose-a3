# Decision Experiments: Variants

We empirically test two architectural decisions on TinyDB `edff96a` using `gemini-3.1-flash-lite` (1 run per cell at temperature 0.2):

## Experiment 1: ADR-001 (Work Splitting — Multi-Agent Pipeline vs. Monolithic 1-Shot)
- **Baseline (`multi_agent`, GitHub Actions)**: 6 specialized stages (`Requirements` -> `Design` -> `Implementation` -> `Testing` -> `Release + CI` -> `Independent Review`), with up to 3 Stage 3/4 retry attempts.
- **Variant (`monolithic`, local via `workflow/autose/eval_monolithic.py`)**: A single agent prompt receives the issue and target source file and directly emits `SEARCH/REPLACE` code edits only (no test generation, no spec/design stage, 1-shot without retries). Uses the exact same `_apply_search_replace` matcher as Stage 3.
- **Evaluation**: Compare build/existing-test pass rates, hidden-test pass rates (`experiment/hidden_tests/`, 21 functions / 51 parametrized cases), and measured tokens across all 5 issues.

## Experiment 2: ADR-008 (Reviewer Independence — Blind Sceptical vs. Canned-Reassurance Shared Context)
- **Baseline (`blind_independent`, local via `workflow/autose/eval_seeded.py`)**: Diff-only review (unlike production Stage 6, `eval_seeded.py` does not run `pytest`). Receives ONLY the original issue and the patch diff, with the sceptical adversarial checklist prompt.
- **Variant (`shared_context`, local via `workflow/autose/eval_seeded.py`)**: Diff-only review receiving a canned reassuring implementer note (`fake_rationale`: *"I carefully analyzed... verified that all existing TinyDB tests pass"*) alongside a neutral review prompt (without the sceptical checklist). Note: this tests susceptibility to reassurance anchoring + prompt framing rather than real implementer conversation logs.
- **Evaluation**: Run both variants on all 5 seeded PRs (`experiment/seeded_prs/pr-1.patch`..`pr-5.patch`) and measure verdict match rate (accuracy) against `labels.csv`. Note: the `tokens` column in `eval_seeded.py` sums both variants (2 calls per PR).
