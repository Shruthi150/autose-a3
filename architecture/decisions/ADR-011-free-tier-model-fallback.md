# ADR-011: Free-Tier `gemini-3.1-flash-lite` Standardization with Quota-Aware Backoff and Logged Fallback

## Status
Accepted (Supersedes [ADR-006](ADR-006-models.md))

## Context
During live GitHub Actions testing of ADR-006:
- `gemini-2.5-flash` returned `404 NOT_FOUND` for new keys.
- `gemini-3.1-pro-preview` had 0 free-tier quota (`429 RESOURCE_EXHAUSTED`).
- `gemini-3.5-flash` and `gemini-3.6-flash` hit daily request caps (~20 RPD) mid-run whenever retries occurred.

## Decision
We standardize all pipeline roles on **`gemini-3.1-flash-lite`** and update `workflow/autose/llm.py` to:
1. Distinguish temporary per-minute `429` limits ($\le 90\text{s}$ `retryDelay`, where it sleeps and retries the same model) from daily quota caps (where it falls back to `gemini-3.5-flash-lite` $\rightarrow$ `gemini-3.5-flash` $\rightarrow$ `gemini-3.6-flash`).
2. Pace calls with a 2-second delay to avoid bursting RPM limits.
3. Explicitly print `[autose-llm] model=<name> tokens=<in>+<out>` on every call so fallback is never silent and token usage is auditable.

Because the reviewer uses the same model under free-tier limits, reviewer independence relies on isolation (separate read-only job, fresh checkout, zero implementer context, sceptical prompt — ADR-008) rather than a different model.

## Consequences
- All 5 GitHub Actions runs and both decision experiments ran at \$0.00 cost under a hard Free-Tier cap.
- Using a single lite model limits single-shot reasoning on complex multi-file changes compared to a Pro model, which we mitigate via short `SEARCH/REPLACE` edit blocks and bounded `pytest` retries.
