# Issue 3: Add Table.upsert_multiple() for efficient batch operations

## Description
Currently, TinyDB has `table.upsert()` for single documents and `table.update_multiple()` for multiple updates, but there is no `table.upsert_multiple()`.

When synchronizing external records in bulk, we have pairs of `(document, condition)`. Calling `table.upsert()` in a loop incurs $N$ separate storage reads and writes, which is very slow and non-atomic.

### Proposed Solution
Add a method `Table.upsert_multiple(updates)` that accepts an iterable of `(document, cond)` pairs:
- If a document matching `cond` exists, update it.
- If not, insert `document` as a new record.
- Perform the batch operation in a SINGLE storage write.
- Return the list of affected document IDs in the exact order of the input.
