# ADR-006: Separate Gemini Flash and Pro Models Across SDLC Stages

## Status
Superseded by [ADR-011](ADR-011-free-tier-model-fallback.md) (early runs with `gemini-2.5-flash`, `gemini-3.5-flash`, `gemini-3.6-flash`, and `gemini-3.1-pro-preview` hit `404 NOT_FOUND` deprecation or free-tier `429 RESOURCE_EXHAUSTED` caps).

## Context
Different SDLC stages have different needs: Requirements, Design, and Testing benefit from fast structured output, while Independent Review benefits from a stronger, separate model to avoid shared blind spots.

Rejected alternative: Using a single uniform model across all stages.

## Decision
Use different Gemini model tiers by role:
- **Flash tier (`gemini-2.5-flash` / `gemini-3.5-flash`)** for Requirements (S1), Design (S2), Implementation (S3), and Testing (S4) for speed and low latency.
- **Pro tier (`gemini-2.5-pro` / `gemini-3.1-pro-preview`)** for the Independent Reviewer (S6) to maximize defect detection and provide model diversity.

## Consequences
- Intended to balance fast inner loops with strong independent review.
- **Outcome in practice**: Failed under a Google AI Studio Free-Tier key because Pro models had 0 free-tier quota and Flash models hit 20-RPD caps, leading to [ADR-011](ADR-011-free-tier-model-fallback.md).
