"""Hidden acceptance tests for issue 4: Query.startswith() / endswith()."""
import pytest
from tinydb import Query

Q = Query()
NAMES = ["John", "Joan", "Mary", "johnny", "", "Jo"]


def _names(table, query):
    return sorted(d["name"] for d in table.search(query))


@pytest.fixture
def table(db):
    t = db.table("t")
    t.insert_multiple([{"name": n} for n in NAMES])
    return t


def test_startswith_matches_prefix_case_sensitively(table):
    assert _names(table, Q.name.startswith("Jo")) == sorted(["Jo", "Joan", "John"])
    assert _names(table, Q.name.startswith("jo")) == ["johnny"]
    assert _names(table, Q.name.startswith("")) == sorted(NAMES)


def test_endswith_matches_suffix_case_sensitively(table):
    assert _names(table, Q.name.endswith("n")) == sorted(["Joan", "John"])
    assert _names(table, Q.name.endswith("Jo")) == ["Jo"]


def test_non_strings_and_missing_fields_never_match_and_never_raise(db):
    t = db.table("mixed")
    t.insert_multiple([{"name": 5}, {"name": None}, {"name": ["Jo"]},
                       {"name": {"x": "Jo"}}, {"other": "Jo"}, {"name": "Jo"}])
    assert [d.get("name") for d in t.search(Q.name.startswith("Jo"))] == ["Jo"]
    assert [d.get("name") for d in t.search(Q.name.endswith("Jo"))] == ["Jo"]


def test_composes_with_other_queries_nested_paths_and_cache(db):
    t = db.table("nested")
    t.insert_multiple([{"user": {"name": "Anna"}, "age": 30},
                       {"user": {"name": "Anton"}, "age": 20},
                       {"user": {"name": "Hanna"}, "age": 40}])
    q_start = Q.user.name.startswith("An")
    q_end = Q.user.name.endswith("nna")
    assert sorted(d["age"] for d in t.search(q_start)) == [20, 30]
    # differs only by method: the query cache must not mix them up
    assert sorted(d["age"] for d in t.search(q_end)) == [30, 40]
    assert [d["age"] for d in t.search(q_start & (Q.age > 25))] == [30]
    assert [d["age"] for d in t.search(~q_start)] == [40]
    assert sorted(d["age"] for d in t.search(q_start | q_end)) == [20, 30, 40]
