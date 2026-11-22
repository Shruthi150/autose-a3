# ADR-001: Specialized Micro-Agents vs. Monolithic Agent

## Status
Accepted

## Context
Our goal is to build an autonomous pipeline that converts a maintainer-triggered issue into a tested, verified, and independently reviewed pull request for TinyDB.
We must decide how to divide the work across the six SDLC stages: Requirements, Design, Implementation, Testing, Release, and Review.

Options:
1. **Single Monolithic Agent**: One general agent handles the entire lifecycle in a single long-running conversation.
2. **Specialized Micro-Agents**: Distinct agents per stage with tailored system prompts, isolated context, and specific tools.

## Decision
We choose **Specialized Micro-Agents**:
- `RequirementsAgent`: Formulates `spec.md` with testable criteria.
- `DesignAgent`: Produces `design.md` identifying files and functions to modify.
- `ImplementationAgent`: Applies code edits to source files.
- `TestingAgent`: Synthesizes tests directly from `spec.md` without seeing the implementer's thought trail.
- `ReleaseAgent`: Deterministic git/GH CLI step opening the PR.
- `IndependentReviewerAgent`: Cold-start sceptical review with zero implementer history.

## Consequences
- Prevents the tester from simply validating what it just wrote (Testing Agent tests against `spec.md`, not against the implementer's reasoning).
- Keeps context windows small, predictable, and cost-effective.
- Requires explicit serialization contracts (`spec.md`, `design.md`) between stages.
