# Specification Skill (Reused from A1)

When turning a raw user issue (bug report, feature request, or vague complaint) into `spec.md`:
1. Separate **observed behaviour** from **expected behaviour**.
2. If the issue is vague or underspecified, explicitly list **Assumptions** chosen to be minimal, idiomatic, and backward-compatible with TinyDB.
3. Define numbered **Acceptance Criteria** (`AC-1`, `AC-2`, ...) in verifiable Given/When/Then or exact input->output form.
4. Always include a `## Public API` section listing exact module/class/method names, parameter names, types, and return values so downstream testing agents can write deterministic tests without guessing.
5. Explicitly specify **error and invalid-input semantics** (whether invalid arguments raise an exception eagerly at construction time or evaluate lazily to `False`, matching TinyDB's existing query conventions).
6. Explicitly call out edge cases: empty inputs, duplicates, non-string types, missing keys, and one-shot iterators/generators.
