"""Hidden acceptance tests for issue 5 (vague): update operations on documents
that do not have the field yet.

The issue deliberately does not say what *should* happen to such documents.
Either reasonable policy passes: start counting from 0, or leave the document
alone. What must never happen is an exception that aborts the whole update.
"""
import pytest
from tinydb import Query
from tinydb.operations import increment, decrement

Q = Query()


@pytest.fixture
def table(db):
    t = db.table("posts")
    t.insert_multiple([
        {"slug": "a", "kind": "post", "views": 10},
        {"slug": "b", "kind": "post"},              # no counter yet
        {"slug": "c", "kind": "post", "views": 0},
        {"slug": "d", "kind": "page"},              # not selected
    ])
    return t


def _by_slug(table):
    return {d["slug"]: dict(d) for d in table.all()}


@pytest.mark.parametrize("op,delta", [(increment, 1), (decrement, -1)])
def test_update_does_not_raise_and_existing_counters_change(table, op, delta):
    table.update(op("views"), Q.kind == "post")
    docs = _by_slug(table)
    assert docs["a"]["views"] == 10 + delta
    assert docs["c"]["views"] == 0 + delta


@pytest.mark.parametrize("op,delta", [(increment, 1), (decrement, -1)])
def test_document_without_field_is_handled_consistently(table, op, delta):
    table.update(op("views"), Q.kind == "post")
    b = _by_slug(table)["b"]
    # Policy 1: starts from 0.  Policy 2: untouched.  Nothing else is valid.
    assert b.get("views", "ABSENT") in (delta, "ABSENT")
    assert b["slug"] == "b" and b["kind"] == "post"


def test_unselected_documents_are_untouched(table):
    table.update(increment("views"), Q.kind == "post")
    assert _by_slug(table)["d"] == {"slug": "d", "kind": "page"}


def test_return_value_and_update_all_still_work(table):
    ids = table.update(increment("views"), Q.kind == "post")
    assert len(ids) == 3
    table.update(increment("views"))  # no condition: every document
    assert _by_slug(table)["a"]["views"] == 12
