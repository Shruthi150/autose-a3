# Issue 1: table.remove() with duplicate doc_ids crashes instead of skipping

## Description
When calling `table.remove(doc_ids=[1, 1])`, TinyDB crashes with an unhandled `KeyError` and fails to remove any documents at all.

According to the docstring for `Table.remove`:
> "If a document ID is not found, it is ignored."

When duplicates are passed in `doc_ids`, the first instance removes the record from storage, but the second evaluation crashes with `KeyError`.

### Reproduction
```python
from tinydb import TinyDB
db = TinyDB('test.json')
table = db.table('dup_test')
ids = table.insert_multiple([{'val': 10}, {'val': 20}])
table.remove(doc_ids=[ids[0], ids[0]]) # Crashes with KeyError
```

### Expected Behavior
Duplicate document IDs should be handled gracefully (deduplicated or ignored if already deleted), removing the document once and returning the list of actually removed IDs without throwing a `KeyError`.
