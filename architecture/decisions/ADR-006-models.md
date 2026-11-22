# ADR-006: Free-Tier Gemini Model Selection and Quota-Aware Fallback

## Status
Superseded by [ADR-011](ADR-011-free-tier-model-fallback.md) (early runs with `gemini-2.5-flash`, `gemini-3.5-flash`, and `gemini-3.6-flash` hit 404 deprecation or 20-RPD free-tier `429 RESOURCE_EXHAUSTED` limits).

## Context
Running six stages across five issues plus decision experiments requires dozens of LLM calls. Under a Google AI Studio Free-Tier API key:
- Pro-tier models (`gemini-3.1-pro`) have 0 free-tier quota.
- `gemini-2.5-flash` is deprecated for new keys (404).
- `gemini-3.5-flash` and `gemini-3.6-flash` hit daily request caps (~20 RPD) quickly when retries occur.

## Decision
We standardize on **`gemini-3.1-flash-lite`** across all roles in `workflow/config.yml`, backed by a quota-aware client (`workflow/autose/llm.py`) with:
- Automatic wait-and-retry on short per-minute (RPM) 429 limits ($\le 90\text{s}$).
- Automatic fallback to `gemini-3.5-flash-lite` $\rightarrow$ `gemini-3.5-flash` $\rightarrow$ `gemini-3.6-flash` only when a daily quota cap is exhausted.
- Gentle 2-second pacing between calls and exact token tracking (`usage_metadata`).

Because the reviewer shares the `gemini-3.1-flash-lite` model family under free-tier constraints, reviewer independence is enforced through **job/context/prompt isolation** (ADR-008) rather than model heterogeneity.

## Consequences
- Zero API cost while maintaining reliable completion of multi-stage runs.
- Slightly lower single-shot reasoning depth than a Pro model, compensated by structured edit blocks (`SEARCH/REPLACE`) and deterministic `pytest` verification loops.
