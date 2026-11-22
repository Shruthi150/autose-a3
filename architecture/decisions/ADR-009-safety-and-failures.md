# ADR-009: Safety, Budgets, Timeouts, and Prompt Injection Defense

## Status
Accepted

## Context
Issues and comments on a public repository can be authored by anyone on the internet, making prompt injection and quota exhaustion primary operational risks.

Rejected alternative: Allowing any public user to trigger workflows directly and interpolating raw issue bodies into shell `run:` blocks.

## Decision
1. **Maintainer Authorization Gate (D10)**: Before any LLM call, `autose.yml` queries `gh api repos/$REPO/collaborators/$ACTOR/permission` and aborts unless the actor has `admin`, `maintain`, or `write` permission.
2. **Untrusted Data Isolation (`security.py`)**: Issue titles and bodies are stripped of null bytes, neutralized against tag breakouts (`</untrusted...>`), truncated to 8,000 chars, and wrapped in `<untrusted_issue_body>...</untrusted_issue_body>` with an explicit system instruction treating them as data only.
3. **Secret Scrubbing & No Persisted Git Credentials**: All 4 job checkouts set `persist-credentials: false` so `GITHUB_TOKEN` is never written to `.git/config`. Subprocesses (`pytest`, `py_compile`) execute under `scrubbed_env()`, stripping `GEMINI_API_KEY` and `GITHUB_TOKEN`; Stage 5 passes `GITHUB_TOKEN` only as an ephemeral `http.extraHeader` to the parent `git push` process.
4. **Auth Before Install**: The collaborator authorization gate runs before checkout and `pip install -e .` so unauthorized actors cannot trigger code installation.
5. **Hard Budgets & Timeouts**:
   - Job timeouts: 20m (`implement_and_release`), 10m (`review`), 15m (`rework`).
   - Implementation-test retries capped at 3; review rounds capped at 2.
   - `diff.patch` edits restricted strictly to `tinydb/*.py` files named in `design.md`; `git add tinydb tests` ensures workflow/architecture files can never be modified by an agent.

## Consequences
- Untrusted users cannot trigger paid/quota LLM runs or exfiltrate repository secrets.
- Bounded retries guarantee runs terminate cleanly even if an issue is too hard.
