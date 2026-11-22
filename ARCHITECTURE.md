# TinyDB Architecture (Pinned at `edff96a`)

TinyDB is a lightweight pure-Python document database organized into seven small modules under `tinydb/`:

- **`tinydb/database.py`**: `TinyDB` class (subclassing `Table` proxy), manages storage instantiation, table registry (`table(name)`, `tables()`, `drop_table()`), and context manager lifecycle.
- **`tinydb/table.py`**: `Table` and `Document` classes. Core CRUD operations: `insert`, `insert_multiple`, `all`, `search`, `get`, `contains`, `update`, `update_multiple`, `upsert`, `remove`, `truncate`, `count`. All mutating operations go through `_update_table(updater)` which reads the table dict, invokes `updater(table)`, clears the query cache (`_query_cache`), and writes back to storage in a single write.
- **`tinydb/queries.py`**: `QueryInstance`, `Query`, `QueryLike`, `where()`. Builds composable predicates (`==`, `!=`, `<`, `>`, `matches`, `search`, `test`, `any`, `all`, `one_of`, `exists`, `fragment`, `&`, `|`, `~`). Each `QueryInstance` carries a test callable and a hashable tuple key (`_hash`) used for query caching.
- **`tinydb/operations.py`**: Transformation helpers for `Table.update()`: `delete`, `add`, `subtract`, `set`, `increment`, `decrement`. Each returns a `Callable[[MutableMapping], None]` that mutates a document in place.
- **`tinydb/storages.py`**: `Storage` ABC, `JSONStorage`, and `MemoryStorage`.
- **`tinydb/middlewares.py`**: `Middleware` base class and `CachingMiddleware`.
- **`tinydb/utils.py`**: `LRUCache`, `FrozenDict`, and `freeze()` helper for making nested structures hashable.

## Key Invariants
1. **Single-write batch operations**: Batch methods (`insert_multiple`, `update_multiple`, `remove`) mutate inside a single `_update_table` call so storage is written once.
2. **Query hashability**: `QueryInstance` objects must have distinct, deterministic hashes (via `freeze()`). One-shot iterators must be materialised so queries remain repeatable and hashable.
3. **Cache invalidation**: `_update_table` clears `_query_cache` automatically; direct storage mutations must never bypass it.
4. **Backward compatibility**: All existing public signatures and return types (`list[Document]` for `all()`/`search()`, `list[int]` for `update()`/`remove()`/`upsert()`) must be preserved.
