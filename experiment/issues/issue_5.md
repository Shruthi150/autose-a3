# Issue 5: update(increment('views'), ...) crashes when field is missing

## Description
Hey, I was trying to use `increment('views')` with `db.update(...)` across all my documents, but it crashed with a `KeyError: 'views'` on documents that don't have that field yet. Can this be fixed so it handles documents without the field?
