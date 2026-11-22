# ADR-006: Heterogeneous Gemini Model Allocation Across SDLC Stages

## Status
Superseded by [ADR-011](ADR-011-free-tier-model-fallback.md) (early runs with `gemini-2.5-flash`, `gemini-3.5-flash`, `gemini-3.6-flash`, and `gemini-3.1-pro-preview` hit `404 NOT_FOUND` deprecation or free-tier `429 RESOURCE_EXHAUSTED` caps).

## Context
Different SDLC stages have different cognitive demands: Requirements, Design, and Testing require fast structured generation, while Independent Review benefits from stronger semantic reasoning and a distinct model family to avoid shared blind spots.

Rejected alternative: Using a single uniform model across all stages.

## Decision
Allocate Google Gemini models heterogeneously:
- **Flash tier (`gemini-2.5-flash` / `gemini-3.5-flash`)** for Requirements (S1), Design (S2), Implementation (S3), and Testing (S4) for speed and low latency.
- **Pro tier (`gemini-2.5-pro` / `gemini-3.1-pro-preview`)** for the Independent Reviewer (S6) to maximize defect detection and provide model diversity.

## Consequences
- Intended to balance fast inner loops with strong independent review.
- **Outcome in practice**: Failed under a Google AI Studio Free-Tier key because Pro models had 0 free-tier quota and Flash models hit 20-RPD caps, leading to [ADR-011](ADR-011-free-tier-model-fallback.md).
