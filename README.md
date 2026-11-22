# AutoSE Assignment 3: Issue In, Pull Request Out

Autonomous multi-agent GitHub Actions workflow that turns a GitHub issue into a tested, CI-verified, and independently reviewed pull request on **TinyDB**.

- **Target Repository**: Pinned copy/import of [msiemens/tinydb](https://github.com/msiemens/tinydb) at commit **`edff96a`** (imported directly from upstream `edff96a` into `Shruthi150/autose-a3`)
- **Model**: Google Gemini **`gemini-3.1-flash-lite`** (free-tier compatible, with RPM backoff and logged fallback to `gemini-3.5-flash-lite` / `gemini-3.5-flash` / `gemini-3.6-flash`)
- **Workflow File**: [`.github/workflows/autose.yml`](.github/workflows/autose.yml) + [`.github/workflows/autose-ci.yml`](.github/workflows/autose-ci.yml)
- **Demo Video**: [`demo.mp4`](demo.mp4) (included in the repository root)

## Cost, Spending Limit & Token Usage
- **Hard Spending Limit**: Runs exclusively on a Google AI Studio **Free-Tier** API key with no billing account attached (hard \$0.00 spending cap enforced by provider).
- **Measured Token Usage**: **`121,339` total measured tokens** (`82,831` across all 5 GitHub Actions build runs: #1 `12,627`, #2 `9,493`, #3 `25,972`, #4 `25,250`, #5 `9,489`; plus `27,073` across Experiment 1 monolithic runs; plus `11,435` across Experiment 2 seeded-PR review calls; excludes Stage 6 reviewer calls on PRs #6–#9 and earlier diagnostic runs; **\$0.00 spent**).
- **Hidden-Test Isolation & Post-Run Hardening**: `experiment/hidden_tests/` was kept outside the repository during all 5 GitHub Actions runs and committed afterward for grading. After the 5 runs, `autose.yml` was further hardened to run `rm -rf experiment/hidden_tests` in all 4 jobs, set `persist-credentials: false` on all checkouts (using an ephemeral push auth header instead of `.git/config`), run the collaborator auth gate before `pip install -e .`, and scope `concurrency` (one pending slot, `cancel-in-progress: false`) to `implement_and_release`.
- **Branch Protection**: `main` and `master` have GitHub branch protection requiring pull requests before merging (repository admins may bypass for direct docs/workflow fixes; workflow bot tokens never push to `main`/`master`).

## How to Trigger the Workflow
A repository maintainer (`admin`, `maintain`, or `write` permission) can trigger the pipeline on any open issue by either:
1. Adding the label **`autose`** to the issue, OR
2. Posting a comment starting with **`/autose`** on the issue.

### Required Repository Setup
1. **Secret**: Add `GEMINI_API_KEY` under **Settings → Secrets and variables → Actions**.
2. **PR Permission**: Enable **Allow GitHub Actions to create and approve pull requests** under **Settings → Actions → General**.
3. **Branch Protection**: Protect the default branch so no bot or user can push directly; only a human maintainer merges PRs.

## Architecture Overview
The pipeline runs across **four GitHub Actions jobs** enforcing least-privilege permissions:
1. **`implement_and_release`** (`contents: write`, `pull-requests: write`, `actions: write`): Runs Stages 1–5 (`spec.md` $\rightarrow$ `design.md` $\rightarrow$ `diff.patch` $\rightarrow$ `test_report.md` $\rightarrow$ `pr.md` + explicit `autose-ci.yml` dispatch).
2. **`review_round_1`** (`contents: read`, `pull-requests: write` — **cannot push**): Fresh checkout of the PR branch; runs Stage 6 independent reviewer on ONLY the issue, `git diff`, and its own `pytest` run (`review.md`).
3. **`rework_round_1`** (conditional on `REQUEST_CHANGES`, `contents: write`): Routes `APPROACH` feedback back to Stage 2 (Design) or `CODE` feedback back to Stage 3 (Implementation), re-tests, pushes, and re-runs CI.
4. **`review_round_2`** (`contents: read`, `pull-requests: write`): Final independent review round (caps review loops at 2).

See [`architecture/views/`](architecture/views/) and [`architecture/decisions/`](architecture/decisions/) for the component view, sequence view, stage map, and all 10 ADRs.

## AI Assistance Disclosure
In accordance with course policy: **DeepSeek** and **Google Gemini (Antigravity)** were used copiously to assist with scaffolding and debugging the Python workflow scripts, GitHub Actions YAML, diagrams, and document/report formatting. All generated files and results were reviewed and verified against real runs, and the original architectural ideas and reasoning behind the decisions are my own.
