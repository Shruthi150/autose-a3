# Architecture Component View

```mermaid
flowchart TD
    subgraph Trigger["GitHub Event & Auth Gate"]
        Ev["issues: [labeled] ('autose') / issue_comment: [created] ('/autose')"]
        Auth["Collaborator Permission Check (admin / maintain / write)"]
        Ev --> Auth
    end

    subgraph Job1["Job 1: implement_and_release (contents: write, pull-requests: write, actions: write)"]
        S1["Stage 1: Requirements Agent\n(A1 spec-skill -> spec.md)"]
        G1{"Check 1: >=2 AC-N + Public API?"}
        S2["Stage 2: Design Agent\n(A2 ARCHITECTURE.md -> design.md)"]
        G2{"Check 2: Existing tinydb/*.py + functions named?"}
        S3["Stage 3: Implementation Agent\n(SEARCH/REPLACE edit blocks -> diff.patch)"]
        G3{"Check 3: py_compile + import tinydb?"}
        S4["Stage 4: Testing Agent\n(spec-only tests + full pytest -> test_report.md)"]
        G4{"Check 4: new + existing pytest pass?"}
        S5["Stage 5: Release (git + gh CLI)\n(push branch, open PR, dispatch autose-ci.yml -> pr.md)"]
        G5{"Check 5: PR open & CI success?"}
    end

    subgraph Job2["Job 2: review_round_1 (contents: read, pull-requests: write — NO PUSH)"]
        S6A["Stage 6: Independent Reviewer\n(Fresh checkout: issue + git diff + own pytest -> review.md)"]
        G6A{"Verdict?"}
    end

    subgraph Job3["Job 3: rework_round_1 (conditional on REQUEST_CHANGES, contents: write)"]
        RW["Route: APPROACH -> Stage 2 | CODE -> Stage 3 -> Stage 4 -> push & CI"]
    end

    subgraph Job4["Job 4: review_round_2 (contents: read, pull-requests: write — NO PUSH)"]
        S6B["Stage 6: Independent Reviewer Round 2\n(Max 2 rounds -> review_round_2.md)"]
    end

    Human["Human Maintainer\n(Final Merge / Close Decision — Never Automated)"]

    Auth --> S1 --> G1
    G1 -- Pass --> S2 --> G2
    G2 -- Pass --> S3 --> G3
    G3 -- Fail --> S3
    G3 -- Pass --> S4 --> G4
    G4 -- "Fail (<=3 attempts)" --> S3
    G4 -- Pass --> S5 --> G5
    G5 -- Pass --> S6A --> G6A
    G6A -- APPROVE --> Human
    G6A -- REQUEST_CHANGES --> RW --> S6B --> Human
```

## Components & Permissions

| Component | Job & GitHub Token Permissions | Inputs | Outputs | Tools |
|---|---|---|---|---|
| **Auth Gate** | `implement_and_release` | `github.actor`, `github.repository` | Pass / Abort | `gh api` collaborator permission |
| **Requirements (S1)** | `implement_and_release` | Wrapped untrusted issue, A1 `spec-skill` | `spec.md` | Gemini API (`gemini-3.1-flash-lite`) |
| **Design (S2)** | `implement_and_release` | `spec.md`, `ARCHITECTURE.md` | `design.md` | Gemini API, file existence check |
| **Implementation (S3)** | `implement_and_release` | `design.md`, target `tinydb/*.py`, failure feedback | `diff.patch` | Gemini API (SEARCH/REPLACE), `py_compile`, `git diff` |
| **Testing (S4)** | `implement_and_release` | `spec.md` only (no design/implementer context) | `test_report.md` | Gemini API, `pytest -o addopts=` in scrubbed env |
| **Release (S5)** | `implement_and_release` | Branch, `spec.md`, `test_report.md` | `pr.md`, PR URL | `git push`, `gh pr create`, `gh workflow run autose-ci.yml` |
| **Reviewer (S6)** | `review_round_1` / `review_round_2` (`contents: read` ONLY) | Issue text, `git diff origin/<base>...HEAD`, own `pytest` | `review.md` | Gemini API, read-only repo + `pytest`, `gh pr comment` |
