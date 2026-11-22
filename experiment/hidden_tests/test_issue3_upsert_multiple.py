"""Hidden acceptance tests for issue 3: Table.upsert_multiple()."""
import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from tinydb.table import Document

Q = Query()


class CountingStorage(MemoryStorage):
    writes = 0

    def write(self, data):
        type(self).writes += 1
        super().write(data)


def test_updates_existing_and_inserts_missing_returning_ids_in_order(db):
    table = db.table("t")
    table.insert_multiple([{"k": "a", "v": 1}, {"k": "b", "v": 1}])
    ids = table.upsert_multiple([
        ({"k": "b", "v": 2}, Q.k == "b"),
        ({"k": "c", "v": 2}, Q.k == "c"),
        ({"k": "a", "v": 2}, Q.k == "a"),
    ])
    assert ids[0] == 2 and ids[2] == 1
    assert ids[1] not in (1, 2)
    assert {d["k"]: d["v"] for d in table.all()} == {"a": 2, "b": 2, "c": 2}
    assert len(table) == 3


def test_whole_batch_is_one_storage_write():
    CountingStorage.writes = 0
    db = TinyDB(storage=CountingStorage)
    table = db.table("t")
    table.insert({"k": 0})
    CountingStorage.writes = 0
    table.upsert_multiple([({"k": i}, Q.k == i) for i in range(10)])
    assert CountingStorage.writes == 1
    assert len(table) == 10


def test_pair_matching_several_documents_updates_all_of_them(db):
    table = db.table("t")
    table.insert_multiple([{"g": 1, "x": 0}, {"g": 1, "x": 0}, {"g": 2, "x": 0}])
    ids = table.upsert_multiple([({"x": 9}, Q.g == 1)])
    assert sorted(ids) == [1, 2]
    assert [d["x"] for d in table.all()] == [9, 9, 0]


def test_document_with_doc_id_and_empty_input(db):
    table = db.table("t")
    table.insert({"a": 1})
    ids = table.upsert_multiple([
        (Document({"a": 2}, doc_id=1), None),
        (Document({"a": 3}, doc_id=50), None),
    ])
    assert ids == [1, 50]
    assert table.get(doc_id=1)["a"] == 2
    assert table.get(doc_id=50)["a"] == 3
    assert table.upsert_multiple([]) == []


def test_missing_cond_without_doc_id_is_rejected_and_nothing_is_written(db):
    table = db.table("t")
    table.insert({"a": 1})
    with pytest.raises(ValueError):
        table.upsert_multiple([({"a": 5}, Q.a == 1), ({"b": 2}, None)])
    assert table.all() == [{"a": 1}]
