# Issue 2: Query.one_of() only matches first document when given generator/iterator

## Description
When using `Query.one_of()` with a generator, iterator, or `map()` object, it matches only the very first document that meets the condition and silently fails to match any subsequent documents.

The docstring states that `one_of` accepts a "list or generator". However, because the iterator is consumed on the first document evaluation, subsequent documents see an empty generator and return `False`.

### Reproduction
```python
from tinydb import TinyDB, Query
db = TinyDB('test.json')
table = db.table('gen_test')
table.insert_multiple([{'color': 'red'}, {'color': 'blue'}])

# Using generator / iterator
colors = (c for c in ['red', 'blue'])
q = Query().color.one_of(colors)
print(table.search(q)) # Returns only [{'color': 'red'}], 'blue' is omitted!
```

### Expected Behavior
`Query.one_of()` should materialise or freeze one-shot iterables so that every document is tested against the full set of options.
