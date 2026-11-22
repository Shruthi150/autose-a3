# Architecture Component View

![Architecture Component View](component_view.png)

## Mermaid Diagram (Source)

```mermaid
flowchart TD
    subgraph Trigger["GitHub Event and Auth Gate"]
        Ev["Event: issue labeled autose or comment /autose"]
        Auth["Collaborator Permission Check (admin, maintain, or write)"]
        Ev --> Auth
    end

    subgraph Job1["Job 1: implement_and_release (contents write, pull-requests write, actions write)"]
        S1["Stage 1: Requirements Agent - spec.md"]
        G1{"Check 1: 2+ AC-N and Public API?"}
        S2["Stage 2: Design Agent - design.md"]
        G2{"Check 2: Existing tinydb files and functions?"}
        S3["Stage 3: Implementation Agent - diff.patch"]
        G3{"Check 3: py_compile and import tinydb?"}
        S4["Stage 4: Testing Agent - test_report.md"]
        G4{"Check 4: new and existing pytest pass?"}
        S5["Stage 5: Release - git push, gh pr create, dispatch CI"]
        G5{"Check 5: PR open and CI success?"}
    end

    subgraph Job2["Job 2: review_round_1 (contents read ONLY - NO PUSH)"]
        S6A["Stage 6: Independent Reviewer - review.md"]
        G6A{"Verdict?"}
    end

    subgraph Job3["Job 3: rework_round_1 (if REQUEST_CHANGES, contents write)"]
        RW["Route APPROACH to Stage 2 or CODE to Stage 3, then Stage 4 and Stage 5"]
    end

    subgraph Job4["Job 4: review_round_2 (contents read ONLY - NO PUSH)"]
        S6B["Stage 6: Independent Reviewer Round 2 (max 2 rounds)"]
    end

    Halt["Halt Run: Write FAILED.md and upload artifacts"]
    Human["Human Maintainer: Final Merge or Close Decision"]

    Auth --> S1
    S1 --> G1
    G1 -- "Fail" --> Halt
    G1 -- "Pass" --> S2
    S2 --> G2
    G2 -- "Fail" --> Halt
    G2 -- "Pass" --> S3
    S3 --> G3
    G3 -- "Fail" --> S3
    G3 -- "Pass" --> S4
    S4 --> G4
    G4 -- "Fail (up to 3 attempts)" --> S3
    G4 -- "Budget Exhausted" --> Halt
    G4 -- "Pass" --> S5
    S5 --> G5
    G5 -- "Fail" --> Halt
    G5 -- "Pass" --> S6A
    S6A --> G6A
    G6A -- "APPROVE" --> Human
    G6A -- "REQUEST_CHANGES" --> RW
    RW --> S6B
    S6B --> Human
```

## Components & Permissions

| Component | Job & GitHub Token Permissions | Inputs | Outputs | Tools |
|---|---|---|---|---|
| **Auth Gate** | `implement_and_release` (runs before checkout/install) | `github.actor`, `github.repository` | Pass / Abort | `gh api` collaborator permission |
| **Requirements (S1)** | `implement_and_release` | Wrapped untrusted issue, A1 `spec-skill` | `spec.md` | Gemini API (`gemini-3.1-flash-lite`) |
| **Design (S2)** | `implement_and_release` | `spec.md`, `ARCHITECTURE.md` | `design.md` | Gemini API, file existence check |
| **Implementation (S3)** | `implement_and_release` | `design.md`, target `tinydb/*.py`, failure feedback | `diff.patch` | Gemini API (`SEARCH/REPLACE`), `py_compile`, `git diff` |
| **Testing (S4)** | `implement_and_release` | `spec.md` only (no design/implementer context) | `test_report.md` | Gemini API, `pytest -o addopts=` in `scrubbed_env` |
| **Release (S5)** | `implement_and_release` | Branch, `spec.md`, `test_report.md` | `pr.md`, PR URL | Ephemeral-header `git push`, `gh pr create`, `gh workflow run autose-ci.yml` |
| **Reviewer (S6)** | `review_round_1` / `review_round_2` (`contents: read` ONLY) | Issue text, `git diff origin/<base>...HEAD`, own `pytest` | `review.md` | Gemini API, read-only repo + `pytest`, `gh pr comment` |
