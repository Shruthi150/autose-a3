# ADR-006: Asymmetric Model Allocation Using Gemini Stack

## Status
Accepted

## Context
Different SDLC stages have varying demands: Requirements, Design, Implementation, and Testing require high speed, low latency, and structured schema following. Independent Review requires adversarial skepticism and edge-case detection.

## Decision
We allocate **Google Gemini models asymmetrically**:
- **Gemini 3.5 Flash**: Assigned to Requirements, Design, Implementation, and Testing. It provides fast response times (<2s), high throughput, and reliable code synthesis.
- **Gemini 3.5 Flash-Lite / Reviewer Profile**: Assigned to the Independent Reviewer with a strict adversarial persona, ensuring distinct prompt dynamics and separate evaluation thresholds.

## Consequences
- Fast execution cycle within GitHub Actions runtime limits (<15 mins).
- Prevents the reviewer from mirroring the implementer's conversational traits.
