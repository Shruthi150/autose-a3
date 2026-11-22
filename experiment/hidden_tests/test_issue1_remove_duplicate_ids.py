"""Hidden acceptance tests for issue 1: remove(doc_ids=...) with duplicate IDs."""
from tinydb import Query

Q = Query()


def _table(db, n=4):
    table = db.table("t")
    ids = table.insert_multiple([{"n": i} for i in range(n)])
    return table, ids


def test_duplicate_ids_do_not_raise_and_doc_is_removed(db):
    table, ids = _table(db)
    table.remove(doc_ids=[ids[0], ids[0]])
    assert [d.doc_id for d in table.all()] == ids[1:]


def test_each_removed_id_is_reported_once(db):
    table, ids = _table(db)
    removed = table.remove(doc_ids=[ids[2], ids[0], ids[2], ids[0], ids[3]])
    assert sorted(removed) == sorted([ids[0], ids[2], ids[3]])
    assert len(removed) == len(set(removed))
    assert [d.doc_id for d in table.all()] == [ids[1]]


def test_duplicates_mixed_with_missing_ids_and_one_shot_iterables(db):
    table, ids = _table(db)
    removed = table.remove(doc_ids=(i for i in [ids[1], 9999, ids[1], 8888]))
    assert removed == [ids[1]]
    assert ids[1] not in [d.doc_id for d in table.all()]
    assert len(table) == 3


def test_regression_unique_ids_still_work(db):
    table, ids = _table(db)
    assert sorted(table.remove(doc_ids=[ids[0], ids[1]])) == sorted(ids[:2])
    assert table.remove(doc_ids=[]) == []
    assert len(table) == 2
