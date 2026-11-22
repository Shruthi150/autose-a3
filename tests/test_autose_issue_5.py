import pytest
from tinydb import TinyDB, Query, where
from tinydb.operations import increment
from tinydb.storages import MemoryStorage

@pytest.fixture
def db():
    return TinyDB(storage=MemoryStorage)

def test_ac1_increment_missing_field(db):
    """AC-1: Given a document without 'views', update(increment('views')) results in 'views': 1."""
    doc_id = db.insert({'name': 'doc1'})
    db.update(increment('views'), doc_ids=[doc_id])
    assert db.get(doc_id=doc_id)['views'] == 1

def test_ac2_increment_existing_field(db):
    """AC-2: Given a document with 'views': 5, update(increment('views')) results in 'views': 6."""
    doc_id = db.insert({'name': 'doc1', 'views': 5})
    db.update(increment('views'), doc_ids=[doc_id])
    assert db.get(doc_id=doc_id)['views'] == 6

def test_ac3_multiple_documents(db):
    """AC-3: Handle multiple documents regardless of whether the field exists."""
    db.insert({'name': 'doc1'})  # No views
    db.insert({'name': 'doc2', 'views': 10})  # Existing views
    
    db.update(increment('views'))
    
    docs = db.all()
    assert docs[0]['views'] == 1
    assert docs[1]['views'] == 11

def test_ac4_no_keyerror_on_missing(db):
    """AC-4: The operation must not raise a KeyError when the field is missing."""
    doc_id = db.insert({'name': 'doc1'})
    try:
        db.update(increment('views'), doc_ids=[doc_id])
    except KeyError:
        pytest.fail("increment() raised KeyError on missing field")

def test_edge_case_empty_db(db):
    """Edge Case: update called on an empty database should perform no action."""
    db.update(increment('views'))
    assert len(db) == 0

def test_edge_case_non_numeric_value(db):
    """Edge Case: Non-numeric existing value should raise TypeError."""
    doc_id = db.insert({'views': 'not_a_number'})
    with pytest.raises(TypeError):
        db.update(increment('views'), doc_ids=[doc_id])

def test_edge_case_negative_step(db):
    """Edge Case: increment('views', -1) on a missing field should result in -1."""
    doc_id = db.insert({'name': 'doc1'})
    # Note: The previous failure indicated a signature mismatch in the test environment.
    # Based on the provided Public API: increment(key: str, step: int = 1)
    db.update(increment('views', -1), doc_ids=[doc_id])
    assert db.get(doc_id=doc_id)['views'] == -1