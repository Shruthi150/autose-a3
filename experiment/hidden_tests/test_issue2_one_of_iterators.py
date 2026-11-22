"""Hidden acceptance tests for issue 2: one_of() with generators / iterators."""
import pytest
from tinydb import Query

Q = Query()
ALLOWED = [1, 3, 4]


def _gen():
    return (x for x in ALLOWED)


@pytest.mark.parametrize("make", [
    _gen,
    lambda: iter(ALLOWED),
    lambda: map(int, ["1", "3", "4"]),
    lambda: filter(None, ALLOWED),
])
def test_one_shot_iterables_match_every_document(db, make):
    table = db.table("t")
    table.insert_multiple([{"a": i} for i in range(1, 6)])
    found = sorted(d["a"] for d in table.search(Q.a.one_of(make())))
    assert found == ALLOWED


def test_same_query_object_gives_same_answer_every_time(db):
    table = db.table("t", cache_size=0)  # cache off: no hiding behind it
    table.insert_multiple([{"a": i} for i in range(1, 6)])
    query = Q.a.one_of(_gen())
    first = sorted(d["a"] for d in table.search(query))
    second = sorted(d["a"] for d in table.search(query))
    assert first == second == ALLOWED


def test_negation_and_combination_with_iterators(db):
    table = db.table("t")
    table.insert_multiple([{"a": i, "b": i % 2} for i in range(1, 6)])
    not_in = sorted(d["a"] for d in table.search(~Q.a.one_of(_gen())))
    assert not_in == [2, 5]
    both = sorted(d["a"] for d in table.search(Q.a.one_of(_gen()) & (Q.b == 1)))
    assert both == [1, 3]


def test_regression_other_collections_still_work(db):
    table = db.table("t")
    table.insert_multiple([{"a": i} for i in range(1, 6)])
    for coll in (ALLOWED, tuple(ALLOWED), set(ALLOWED), frozenset(ALLOWED),
                 {1: 0, 3: 0, 4: 0}):
        assert sorted(d["a"] for d in table.search(Q.a.one_of(coll))) == ALLOWED
