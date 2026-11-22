# AutoSE Assignment 3: Issue In, Pull Request Out

Autonomous multi-agent GitHub Actions workflow that turns a GitHub issue into a tested, CI-verified, and independently reviewed pull request on **TinyDB**.

- **Target Repository**: Fork of [msiemens/tinydb](https://github.com/msiemens/tinydb) pinned at commit **`edff96a`**
- **Model**: Google Gemini **`gemini-3.1-flash-lite`** (free-tier compatible, with automatic RPM backoff and fallback to `gemini-3.5-flash-lite` / `gemini-3.5-flash`)
- **Workflow File**: [`.github/workflows/autose.yml`](.github/workflows/autose.yml) + [`.github/workflows/autose-ci.yml`](.github/workflows/autose-ci.yml)

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
In accordance with course policy: AI coding assistants (Google Antigravity / Gemini & Claude) were used to help scaffold and debug the Python workflow scripts, GitHub Actions YAML, and documentation formatting. All architectural trade-offs, ADR reasoning, and experimental evaluations were reviewed and verified against real executions.
