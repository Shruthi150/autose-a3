# Issue 4: Add Query.startswith() and Query.endswith() string matchers

## Description
Querying string fields with prefix or suffix checks currently requires verbose regex queries (`Query().name.matches(r'^Jo')`) or custom test functions. When trying `Query().name.startswith('Jo')`, TinyDB raises `RuntimeError: Empty query was evaluated`.

### Proposed Solution
Support native `.startswith(prefix)` and `.endswith(suffix)` methods on `Query` paths:
- `Query().field.startswith('prefix')`
- `Query().field.endswith('suffix')`
- Non-string field values should cleanly evaluate to `False` without raising `AttributeError` or crashing.
